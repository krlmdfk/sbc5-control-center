#!/usr/bin/env python3
"""Isolated offline SBC5 3.2.1 canary: inspect only, never control fans.

No Home Assistant API, Supervisor token, GPIO, config mount, or writes to /share.
Accept only a manually supplied release inspection ZIP and optional copy of a
model in /share/sbc5_canary/. Never execute code from the inspected ZIP.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import zipfile

INPUT = Path("/share/sbc5_canary")
ARCHIVE = INPUT / "SBC5_3.2.1_OFFLINE_INSPECTION_ONLY.zip"
MODEL_COPY = INPUT / "ai_cooling_model.json"
MAX_ARCHIVE_SIZE = 30 * 1024 * 1024
MAX_MANIFEST_SIZE = 2 * 1024 * 1024
MAX_MODEL_SIZE = 16 * 1024 * 1024
MAX_MEMBERS = 4096
MAX_MEMBER_SIZE = 128 * 1024 * 1024
MAX_UNCOMPRESSED = 512 * 1024 * 1024

REQUIRED_RUNTIME_FILES = {
    "local_apps/sbc5_control_center/ai_model_lock.py",
    "local_apps/sbc5_control_center/ai_model_diagnostics.py",
    "local_apps/sbc5_control_center/zip_security_preflight.py",
    "local_apps/sbc5_control_center/ai_cooling_v5.py",
    "local_apps/sbc5_control_center/ai_cooling_v5_1.py",
    "local_apps/sbc5_control_center/ai_cooling_v5_2.py",
    "local_apps/sbc5_control_center/migration_manager_v2.py",
    "local_apps/sbc5_control_center/thermal_effectiveness.py",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for data in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(data)
    return digest.hexdigest()


def regular_file(path: Path, limit: int) -> bool:
    try:
        info = path.lstat()
        return stat.S_ISREG(info.st_mode) and 0 < info.st_size <= limit
    except OSError:
        return False


def safe_member(info: zipfile.ZipInfo) -> bool:
    name = info.filename
    if not name or name.startswith("/") or "\\" in name or "\x00" in name:
        return False
    if any(segment in ("", ".", "..") for segment in name.split("/")):
        return False
    mode = info.external_attr >> 16
    kind = stat.S_IFMT(mode)
    if kind not in (0, stat.S_IFREG):
        return False
    if info.is_dir() or info.flag_bits & 1 or info.file_size > MAX_MEMBER_SIZE:
        return False
    return not (
        info.file_size > 1024 * 1024
        and info.file_size > max(1, info.compress_size) * 2000
    )


def inspect_archive(path: Path) -> dict:
    if not regular_file(path, MAX_ARCHIVE_SIZE):
        raise ValueError("Brak pliku ZIP lub rozmiar poza limitem 30 MiB")
    actual_archive_sha = sha256_file(path)
    with zipfile.ZipFile(path, "r") as archive:
        infos = archive.infolist()
        if not infos or len(infos) > MAX_MEMBERS:
            raise ValueError("ZIP ma nieprawidłową liczbę plików")
        names = [item.filename for item in infos]
        if len(names) != len(set(names)) or any(not safe_member(item) for item in infos):
            raise ValueError("ZIP zawiera duplikaty lub niedozwolone ścieżki")
        if sum(item.file_size for item in infos) > MAX_UNCOMPRESSED:
            raise ValueError("ZIP przekracza bezpieczny rozmiar")
        meta = archive.getinfo("update-manifest.json")
        if meta.file_size > MAX_MANIFEST_SIZE:
            raise ValueError("Manifest jest za duży")
        with archive.open(meta) as stream:
            manifest = json.loads(stream.read(MAX_MANIFEST_SIZE + 1))
        if not isinstance(manifest, dict) or manifest.get("version") != "3.2.1":
            raise ValueError("Wersja manifestu nie jest 3.2.1")
        files = manifest.get("files")
        if not isinstance(files, dict) or not files:
            raise ValueError("Brak listy kontrolnej plików")
        expected = set(files) | {"update-manifest.json"}
        if expected != set(names):
            raise ValueError("Zawartość ZIP różni się od manifestu")
        if not REQUIRED_RUNTIME_FILES.issubset(files):
            raise ValueError("W ZIP brakuje modułów AI lub zabezpieczeń")
        for name, wanted in files.items():
            if not isinstance(name, str) or not re.fullmatch("[0-9a-fA-F]{64}", str(wanted)):
                raise ValueError("Nieprawidłowy wpis manifestu")
            digest = hashlib.sha256()
            with archive.open(name) as member:
                for chunk in iter(lambda: member.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest().lower() != wanted.lower():
                raise ValueError("Niepoprawna suma SHA-256: " + name)
        release_file = "local_apps/sbc5_control_center/release.json"
        release = json.loads(archive.read(release_file))
        if release.get("version") != "3.2.1" or release.get("package_version") != "3.2.1":
            raise ValueError("Metadane release.json nie zgadzają się z 3.2.1")
    return {
        "version": "3.2.1",
        "validated_files": len(files),
        "archive_sha256": actual_archive_sha,
        "archive_bytes": path.stat().st_size,
        "result": "PASS",
    }


def inspect_model_copy(path: Path) -> dict:
    if not regular_file(path, MAX_MODEL_SIZE):
        return {"present": False, "note": "Nie dostarczono opcjonalnej kopii modelu AI"}
    report = {"present": True, "bytes": path.stat().st_size, "sha256": sha256_file(path)}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Model JSON musi być obiektem")
        for key in ("schema", "observations_total", "qualified_samples_total",
                    "migrated_from_schema", "legacy_samples_total"):
            value = data.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                report[key] = value
        report["has_hierarchical_v5"] = isinstance(data.get("hierarchical_v5"), dict)
        report["result"] = "PASS"
    except (OSError, ValueError, UnicodeError):
        report["result"] = "INVALID_JSON"
    return report


def main() -> int:
    print("SBC5 Canary 3.2.1 — OFFLINE / READ-ONLY / NO FAN CONTROL", flush=True)
    print("Nie uruchamiam GPIO, AI PWM ani usług Home Assistant.", flush=True)
    result = {
        "mode": "offline_inspection_only",
        "fan_controller_started": False,
        "shared_config_modified": False,
    }
    try:
        result["archive"] = inspect_archive(ARCHIVE)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, RuntimeError, TypeError) as exc:
        # Never leak contents from the user-provided archive into logs.
        result["archive"] = {"result": "FAIL", "error_type": type(exc).__name__}
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
        return 1
    result["model_copy"] = inspect_model_copy(MODEL_COPY)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
