#!/usr/bin/env python3
"""Simulate a 3.2.0 -> 3.2.1-rc2 Store canary handoff without touching HAOS."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "local_apps" / "sbc5_control_center" / "migration_manager_v2.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    spec = importlib.util.spec_from_file_location("sbc5_upgrade_321_canary", MODULE)
    assert spec is not None and spec.loader is not None
    mm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mm)

    assert mm.semver("3.2.1-rc2") is not None
    assert mm.semver("3.2.0") < mm.semver("3.2.1-rc1")
    assert mm.semver("3.2.1-rc1") < mm.semver("3.2.1-rc2")
    assert mm.semver("3.2.1-rc2") < mm.semver("3.2.1-rc10")
    assert mm.semver("3.2.1-rc10") < mm.semver("3.2.1")
    assert mm.semver("3.2.1-beta.2+build.8") < mm.semver("3.2.1-rc2")
    assert mm.semver("3.2.1-rc.02") is None
    assert mm.semver("3.2") is None

    source_slug = "aaaa_stable_sbc5_control_center"
    target_slug = "bbbb_rc_sbc5_control_center"
    apps = [
        {"slug": source_slug, "state": "stopped", "installed": True, "version": "3.2.0"},
        {"slug": target_slug, "state": "stopped", "installed": True, "version": "3.2.1-rc2"},
    ]
    mm.installed_apps = lambda: apps
    assert mm.select_target(source_slug, "3.2.0") == (target_slug, "3.2.1-rc2", "canary_test")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        source = root / "source"
        data = root / "target"
        shared = root / "shared"
        handoff = shared / "store_handoff_v1"
        source.mkdir()
        data.mkdir()
        model = {"schema": 5, "observations_total": 40072,
                 "qualified_samples_total": 1169,
                 "hierarchical_v5": {"targets": {"50": {"learned": True}}},
                 "thermal_predictor": {"accepted_samples_total": 196818}}
        source_options = {
            "section_ai_cooling_enabled": True,
            "ai_cooling_mode": "assist",
            "section_cpu_enabled": True,
            "config_cpu_profile": "mild",
            "config_cpu": {"arm_freq": 2500},
            "section_gpu_enabled": True,
            "config_gpu_profile": "balanced",
            "custom_target_c": 49.0,
            "custom_curve_editor": {"name": "custom1", "hysteresis": 0.75},
        }
        target_options = {"config_cpu_profile": "factory", "section_cpu_enabled": False,
                          "some_new_default": {"enabled": True}}
        write(source / "ai_cooling_model.json", model)
        write(source / "options.json", source_options)
        write(source / "cpu_profile_state.json", {"requested_profile": "mild"})
        write(source / "gpu_profile_state.json", {"requested_profile": "balanced"})
        write(source / "custom_curve_editor.json", {"target_c": 49.0, "name": "custom1"})
        write(data / "options.json", target_options)
        write(data / "ai_cooling_model.json", {"schema": 5, "observations_total": 12})
        old_model_sha = sha(data / "ai_cooling_model.json")
        old_options_sha = sha(data / "options.json")

        mm.DATA = data
        mm.SHARED_PARENT = shared
        mm.HANDOFF = handoff
        mm.READY = handoff / "READY"
        mm.MANIFEST = handoff / "manifest.json"
        mm.PAYLOAD = handoff / "payload"
        mm.COMPLETE = handoff / "COMPLETE.json"
        mm.CANARY_COMPLETE = handoff / "CANARY_COMPLETE.json"
        mm.STATUS = data / "store_migration_status.json"
        mm.IMPORT_MARKER = data / "store_migration_import.json"
        mm.BACKUP_ROOT = data / "migration_backups"
        mm.PROFILE_SYNC_MARKER = data / "profile_supervisor_sync_state.json"
        mm.PROFILE_MIGRATION_GUARD = data / "store_migration_profile_guard.json"
        mm.self_slug = lambda: source_slug
        mm.channel = lambda _slug: "store"
        mm.app_state = lambda _slug: "stopped"
        mm.collect_payload = lambda source_root, dst_root: original_collect(source, dst_root)

        assert mm.export_handoff("3.2.0") == 0
        manifest = json.loads(mm.MANIFEST.read_text(encoding="utf-8"))
        assert manifest["source_version"] == "3.2.0"
        assert manifest["target_version"] == "3.2.1-rc2"
        assert manifest["mode"] == "canary_test"
        assert "ai_cooling_model.json" in manifest["files"]
        source_hash = sha(source / "ai_cooling_model.json")
        assert sha(mm.PAYLOAD / "ai_cooling_model.json") == source_hash

        mm.self_slug = lambda: target_slug
        assert mm.import_handoff("3.2.1-rc1") == 20
        assert json.loads(mm.STATUS.read_text(encoding="utf-8"))["state"] == "import_waiting_target_version"
        assert sha(data / "ai_cooling_model.json") == old_model_sha
        assert sha(data / "options.json") == old_options_sha
        assert mm.import_handoff("3.2.1") == 20
        assert sha(data / "ai_cooling_model.json") == old_model_sha

        # Wrong target ownership must not restore a foreign handoff.
        mm.self_slug = lambda: "cccc_other_sbc5_control_center"
        assert mm.import_handoff("3.2.1-rc2") == 0
        assert json.loads(mm.STATUS.read_text(encoding="utf-8"))["state"] == "import_skipped_foreign_handoff"
        assert sha(data / "ai_cooling_model.json") == old_model_sha

        mm.self_slug = lambda: target_slug
        assert mm.import_handoff("3.2.1-rc2") == 0
        assert sha(data / "ai_cooling_model.json") == source_hash
        imported = json.loads((data / "ai_cooling_model.json").read_text(encoding="utf-8"))
        assert imported["observations_total"] == 40072
        assert imported["qualified_samples_total"] == 1169
        assert imported["hierarchical_v5"] == model["hierarchical_v5"]
        assert imported["thermal_predictor"] == model["thermal_predictor"]
        options = json.loads((data / "options.json").read_text(encoding="utf-8"))
        assert options["config_cpu_profile"] == "mild"
        assert options["config_gpu_profile"] == "balanced"
        assert options["config_cpu"]["arm_freq"] == 2500
        assert options["custom_target_c"] == 49.0
        assert options["some_new_default"] == {"enabled": True}
        assert json.loads(mm.IMPORT_MARKER.read_text())["target_version"] == "3.2.1-rc2"
        assert mm.CANARY_COMPLETE.is_file()

        # Reimport with unchanged fingerprint must be idempotent.
        assert mm.import_handoff("3.2.1-rc2") == 0
        assert sha(data / "ai_cooling_model.json") == source_hash

        assert mm.rollback() == 0
        assert sha(data / "ai_cooling_model.json") == old_model_sha
        assert sha(data / "options.json") == old_options_sha
        assert not mm.IMPORT_MARKER.exists()

    print("3.2.0 -> 3.2.1-rc2 canary AI/profile preservation: PASS")


def original_collect(source: Path, destination: Path):
    # Exact production code path, but with an isolated source directory.
    spec = importlib.util.spec_from_file_location("sbc5_upgrade_collector", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.collect_payload(source, destination)


if __name__ == "__main__":
    main()
