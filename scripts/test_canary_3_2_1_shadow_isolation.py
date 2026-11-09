#!/usr/bin/env python3
"""Isolated canary tests: no controller launch, only ZIP + copied JSON validation."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center_canary"
MODULE = APP / "canary_runner.py"
spec = importlib.util.spec_from_file_location("sbc5_shadow_canary_runtime", MODULE)
assert spec and spec.loader
canary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(canary)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    archive_path = root / "SBC5_3.2.1_OFFLINE_INSPECTION_ONLY.zip"
    payload = {
        name: f"isolated dummy {name}".encode()
        for name in canary.REQUIRED_RUNTIME_FILES
    }
    payload["local_apps/sbc5_control_center/release.json"] = (
        b'{"version":"3.2.1","package_version":"3.2.1"}'
    )
    manifest = {"version": "3.2.1", "files": {name: sha(raw) for name, raw in payload.items()}}
    def build_zip(replacement=None, extra=None):
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as package:
            package.writestr("update-manifest.json", json.dumps(manifest))
            for name, raw in payload.items():
                package.writestr(name, replacement if name == "local_apps/sbc5_control_center/ai_model_lock.py" and replacement is not None else raw)
            if extra:
                package.writestr(extra, b"unexpected")

    build_zip()
    digest = sha(archive_path.read_bytes())
    original = archive_path.read_bytes()
    report = canary.inspect_archive(archive_path)
    assert report["version"] == "3.2.1"
    assert report["validated_files"] == len(payload)
    assert report["archive_sha256"] == digest
    assert archive_path.read_bytes() == original

    model = root / "ai_cooling_model.json"
    seed = {"schema": 5, "observations_total": 40072,
            "qualified_samples_total": 1169,
            "hierarchical_v5": {"secret_training_blob": [1, 2, 3]}}
    model.write_text(json.dumps(seed))
    original_model = model.read_bytes()
    model_report = canary.inspect_model_copy(model)
    assert model_report["result"] == "PASS"
    assert model_report["observations_total"] == 40072
    assert model_report["qualified_samples_total"] == 1169
    assert model.read_bytes() == original_model
    assert "secret_training_blob" not in json.dumps(model_report)

    model.unlink()
    model.symlink_to(archive_path)
    assert canary.inspect_model_copy(model)["present"] is False
    model.unlink()

    build_zip(replacement=b"intentionally altered")
    try:
        canary.inspect_archive(archive_path)
    except ValueError:
        pass
    else:
        raise AssertionError("tampered ZIP allowed")
    build_zip(extra="../escape")
    try:
        canary.inspect_archive(archive_path)
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe ZIP path allowed")

cfg = (APP / "config.yaml").read_text(encoding="utf-8")
docker = (APP / "Dockerfile").read_text(encoding="utf-8")
assert "boot: manual" in cfg
assert "full_access: false" in cfg
assert "host_pid: false" in cfg
assert "homeassistant_api: false" in cfg
assert "hassio_api: false" in cfg
assert "read_only: true" in cfg
assert "startup: application" in cfg
assert 'ENTRYPOINT ["python3", "-B", "/canary_runner.py"]' in docker
assert "run_legacy.sh" not in docker
assert "sbc5-core" not in docker
assert "privileged:" not in cfg
assert "SYS_ADMIN" not in cfg
print("SBC5 isolated read-only Canary security and archive checks: PASS")
