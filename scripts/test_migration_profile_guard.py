#!/usr/bin/env python3
"""Regression test for Local -> Store profile finalization guard."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "local_apps" / "sbc5_control_center" / "migration_manager.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    spec = importlib.util.spec_from_file_location("sbc5_migration_manager_test", MODULE_PATH)
    assert spec and spec.loader
    mm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mm)

    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        data = base / "data"
        shared = base / "shared"
        handoff = shared / "store_handoff_v1"
        payload = handoff / "payload"
        data.mkdir()
        payload.mkdir(parents=True)

        mm.DATA = data
        mm.SHARED_PARENT = shared
        mm.HANDOFF = handoff
        mm.READY = handoff / "READY"
        mm.MANIFEST = handoff / "manifest.json"
        mm.PAYLOAD = payload
        mm.COMPLETE = handoff / "COMPLETE.json"
        mm.STATUS = data / "store_migration_status.json"
        mm.IMPORT_MARKER = data / "store_migration_import.json"
        mm.BACKUP_ROOT = data / "migration_backups"
        mm.PROFILE_SYNC_MARKER = data / "profile_supervisor_sync_state.json"
        mm.PROFILE_MIGRATION_GUARD = data / "store_migration_profile_guard.json"

        store_defaults = {
            "section_cpu_enabled": False,
            "config_cpu_profile": "factory",
            "config_cpu": {},
            "section_gpu_enabled": False,
            "config_gpu_profile": "factory",
            "config_gpu": {},
            "config_txt_manager": {"enabled": False},
        }
        write_json(data / "options.json", store_defaults)
        write_json(mm.PROFILE_SYNC_MARKER, {"signature": "stale-store-default-signature"})

        source_options = {
            "section_cpu_enabled": True,
            "config_cpu_profile": "mild",
            "config_cpu": {"arm_freq": 2500},
            "section_gpu_enabled": True,
            "config_gpu_profile": "balanced",
            "config_gpu": {"core_freq": 950, "isp_freq": 950, "v3d_freq": 1000},
            "config_txt_manager": {"enabled": True},
        }
        write_json(payload / "options.json", source_options)
        write_json(payload / "cpu_profile_state.json", {"enabled": True, "requested_profile": "mild", "requested_config": {"arm_freq": 2500}})
        write_json(payload / "gpu_profile_state.json", {"enabled": True, "requested_profile": "balanced", "requested_config": {"core_freq": 950, "isp_freq": 950, "v3d_freq": 1000}})

        files = {p.name: digest(p) for p in payload.iterdir() if p.is_file()}
        fp = mm.fingerprint(files)
        manifest = {
            "schema": 1,
            "source_slug": "local_sbc5_control_center",
            "source_version": "2.8.30",
            "target_slug": "98b55775_sbc5_control_center",
            "created_at": mm.now_iso(),
            "files": files,
            "fingerprint": fp,
        }
        write_json(mm.MANIFEST, manifest)
        mm.READY.write_text(fp + "\n", encoding="utf-8")

        mm.self_slug = lambda: "98b55775_sbc5_control_center"
        mm.local_source_state = lambda current: ("local_sbc5_control_center", "stopped")

        rc = mm.import_handoff("2.8.31")
        assert rc == 0, rc
        guard = json.loads(mm.PROFILE_MIGRATION_GUARD.read_text(encoding="utf-8"))
        assert guard["state"] == "pending"
        assert guard["source_fingerprint"] == fp
        assert not mm.PROFILE_SYNC_MARKER.exists(), "stale Supervisor profile marker survived import"
        merged = json.loads((data / "options.json").read_text(encoding="utf-8"))
        assert merged["config_cpu_profile"] == "mild" and merged["section_cpu_enabled"] is True
        assert merged["config_gpu_profile"] == "balanced" and merged["section_gpu_enabled"] is True
        marker = json.loads(mm.IMPORT_MARKER.read_text(encoding="utf-8"))
        assert marker["profile_sync_guard"] == "pending"

        rc = mm.rollback()
        assert rc == 0, rc
        restored = json.loads((data / "options.json").read_text(encoding="utf-8"))
        assert restored["config_cpu_profile"] == "factory"
        assert restored["config_gpu_profile"] == "factory"
        assert mm.PROFILE_SYNC_MARKER.exists(), "rollback did not restore pre-import Supervisor marker"
        assert not mm.PROFILE_MIGRATION_GUARD.exists(), "rollback left migration guard behind"

    print("Migration profile guard regression PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
