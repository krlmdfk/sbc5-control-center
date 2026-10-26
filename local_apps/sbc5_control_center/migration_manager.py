#!/usr/bin/env python3
"""SBC5 local -> Home Assistant Apps migration handoff.

The migration never reaches into another app's private data directory. The source
instance exports an allow-listed snapshot to the shared Home Assistant config tree;
the store-managed instance verifies hashes and imports it before the controller starts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DATA = Path("/data")
SHARED_PARENT = Path("/homeassistant/sbc5_control_center/migration")
HANDOFF = SHARED_PARENT / "store_handoff_v1"
READY = HANDOFF / "READY"
MANIFEST = HANDOFF / "manifest.json"
PAYLOAD = HANDOFF / "payload"
COMPLETE = HANDOFF / "COMPLETE.json"
STATUS = DATA / "store_migration_status.json"
IMPORT_MARKER = DATA / "store_migration_import.json"
BACKUP_ROOT = DATA / "migration_backups"

# Only durable user state. Runtime locks, restart markers, update state and cached
# telemetry are intentionally excluded.
MIGRATE_FILES = (
    "ai_cooling_model.json",
    "ai_grid_profile.json",
    "fan_calibration.json",
    "cpu_profile_state.json",
    "gpu_profile_state.json",
    "custom_curve_editor.json",
    "custom_curve_config_signature",
    "last_fan_profile_code",
    "fan_profile_reconcile.json",
    "options.json",
    "sbc5_system_defaults_lock",
    "sbc5cc-managed.absent",
)


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass


def write_status(state: str, **extra: Any) -> None:
    payload = {"state": state, "updated_at": now_iso(), **extra}
    atomic_json(STATUS, payload)
    # Shared mirror helps the old and new identities see the same migration state.
    try:
        atomic_json(SHARED_PARENT / "store_handoff_status.json", payload)
    except OSError:
        pass


def supervisor_get(path: str) -> dict[str, Any]:
    token = os.environ.get("SUPERVISOR_TOKEN", "")
    if not token:
        return {}
    req = urllib.request.Request(
        "http://supervisor" + path,
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            return raw if isinstance(raw, dict) else {}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return {}


def installed_apps() -> list[dict[str, Any]]:
    raw = supervisor_get("/addons")
    data = raw.get("data") if isinstance(raw.get("data"), dict) else raw
    apps = data.get("addons", []) if isinstance(data, dict) else []
    return [x for x in apps if isinstance(x, dict)]


def self_slug() -> str:
    raw = supervisor_get("/addons/self/info")
    data = raw.get("data") if isinstance(raw.get("data"), dict) else raw
    if isinstance(data, dict) and data.get("slug"):
        return str(data["slug"])
    # Fallback is intentionally conservative. A store identity has a repository prefix.
    for app in installed_apps():
        if str(app.get("name", "")) == "SBC5 Control Center" and str(app.get("state", "")) in {"started", "running"}:
            return str(app.get("slug", ""))
    return "local_sbc5_control_center"


def channel(slug: str) -> str:
    if slug.startswith("local_"):
        return "local"
    if slug.endswith("_sbc5_control_center"):
        return "store"
    return "unknown"


def sibling_store_slug(current: str) -> str:
    for app in installed_apps():
        slug = str(app.get("slug", ""))
        if slug != current and slug.endswith("_sbc5_control_center") and not slug.startswith("local_"):
            if app.get("installed", True):
                return slug
    return ""


def local_source_state(current: str) -> tuple[str, str]:
    for app in installed_apps():
        slug = str(app.get("slug", ""))
        if slug == current:
            continue
        if slug in {"local_sbc5_control_center", "local_rpi5_fan_manager"}:
            return slug, str(app.get("state", ""))
    return "", ""


def store_state(slug: str) -> str:
    for app in installed_apps():
        if str(app.get("slug", "")) == slug:
            return str(app.get("state", ""))
    return ""


def collect_payload(src_root: Path, dst_root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    dst_root.mkdir(parents=True, exist_ok=True)
    for name in MIGRATE_FILES:
        src = src_root / name
        if not src.exists() or not src.is_file() or src.is_symlink():
            continue
        dst = dst_root / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        hashes[name] = sha256(dst)
    return hashes


def fingerprint(hashes: dict[str, str]) -> str:
    raw = "\n".join(f"{k}\t{hashes[k]}" for k in sorted(hashes)).encode()
    return hashlib.sha256(raw).hexdigest()


def export_handoff(version: str) -> int:
    current = self_slug()
    if channel(current) != "local":
        write_status("export_skipped_not_local", current_slug=current)
        return 0

    if COMPLETE.exists():
        try:
            done = json.loads(COMPLETE.read_text(encoding="utf-8"))
        except Exception:
            done = {}
        if done.get("source_slug") == current:
            write_status("source_deprecated_after_store_migration", current_slug=current, target_slug=done.get("target_slug", ""))
            return 21

    target = sibling_store_slug(current)
    if not target:
        write_status("export_skipped_no_store_target", current_slug=current)
        return 0
    if store_state(target) in {"started", "running"}:
        write_status("export_blocked_store_running", current_slug=current, target_slug=target)
        return 22

    SHARED_PARENT.mkdir(parents=True, exist_ok=True)
    tmp = SHARED_PARENT / f".store_handoff_v1.tmp.{os.getpid()}"
    shutil.rmtree(tmp, ignore_errors=True)
    (tmp / "payload").mkdir(parents=True)
    hashes = collect_payload(DATA, tmp / "payload")
    if not hashes:
        shutil.rmtree(tmp, ignore_errors=True)
        write_status("export_failed_empty", current_slug=current, target_slug=target)
        return 3
    manifest = {
        "schema": 1,
        "source_slug": current,
        "source_version": version,
        "target_slug": target,
        "created_at": now_iso(),
        "files": hashes,
        "fingerprint": fingerprint(hashes),
    }
    atomic_json(tmp / "manifest.json", manifest)
    (tmp / "READY").write_text(manifest["fingerprint"] + "\n", encoding="utf-8")
    shutil.rmtree(HANDOFF, ignore_errors=True)
    os.replace(tmp, HANDOFF)
    write_status("export_ready", **manifest)
    print(json.dumps({"result": "export_ready", **manifest}, ensure_ascii=False))
    return 0


def verify_handoff(current: str) -> tuple[dict[str, Any], str]:
    if not READY.is_file() or not MANIFEST.is_file() or not PAYLOAD.is_dir():
        raise RuntimeError("handoff_not_ready")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("schema") != 1:
        raise RuntimeError("unsupported_schema")
    target = str(manifest.get("target_slug", ""))
    if target and target != current:
        raise RuntimeError(f"wrong_target:{target}")
    hashes = manifest.get("files")
    if not isinstance(hashes, dict) or not hashes:
        raise RuntimeError("empty_manifest")
    checked: dict[str, str] = {}
    for name, expected in hashes.items():
        if name not in MIGRATE_FILES:
            raise RuntimeError(f"unexpected_file:{name}")
        p = PAYLOAD / name
        if not p.is_file() or p.is_symlink():
            raise RuntimeError(f"missing_file:{name}")
        got = sha256(p)
        if got != expected:
            raise RuntimeError(f"hash_mismatch:{name}")
        checked[name] = got
    fp = fingerprint(checked)
    if fp != manifest.get("fingerprint"):
        raise RuntimeError("fingerprint_mismatch")
    return manifest, fp


def deep_merge(base: Any, incoming: Any) -> Any:
    if isinstance(base, dict) and isinstance(incoming, dict):
        out = dict(base)
        for key, value in incoming.items():
            out[key] = deep_merge(out.get(key), value) if key in out else value
        return out
    return incoming


def backup_current(names: list[str], fingerprint_value: str) -> Path:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    backup = BACKUP_ROOT / f"store_import_{stamp}"
    backup.mkdir(parents=True)
    existed: list[str] = []
    for name in names:
        p = DATA / name
        if p.is_file() and not p.is_symlink():
            shutil.copy2(p, backup / name)
            existed.append(name)
    atomic_json(backup / "backup_manifest.json", {"created_at": now_iso(), "existed": existed, "source_fingerprint": fingerprint_value})
    return backup


def import_handoff(version: str) -> int:
    current = self_slug()
    if channel(current) != "store":
        write_status("import_skipped_not_store", current_slug=current)
        return 0
    if IMPORT_MARKER.exists():
        try:
            marker = json.loads(IMPORT_MARKER.read_text(encoding="utf-8"))
            if marker.get("source_fingerprint"):
                write_status("import_already_complete", current_slug=current, **marker)
                return 0
        except Exception:
            pass
    if not READY.exists():
        write_status("import_skipped_no_handoff", current_slug=current)
        return 0

    source_slug, source_state = local_source_state(current)
    if source_slug and source_state in {"started", "running"}:
        write_status("import_waiting_source_stop", current_slug=current, source_slug=source_slug, source_state=source_state)
        return 20

    try:
        manifest, fp = verify_handoff(current)
    except Exception as exc:
        write_status("import_verification_failed", current_slug=current, error=str(exc))
        return 4

    names = sorted(str(x) for x in manifest["files"])
    backup = backup_current(names, fp)
    imported: list[str] = []
    try:
        for name in names:
            src = PAYLOAD / name
            dst = DATA / name
            if name == "options.json":
                try:
                    current_options = json.loads(dst.read_text(encoding="utf-8")) if dst.is_file() else {}
                    source_options = json.loads(src.read_text(encoding="utf-8"))
                    merged = deep_merge(current_options, source_options)
                    atomic_json(dst, merged)
                except Exception:
                    shutil.copy2(src, dst)
            else:
                tmp = DATA / (name + ".migration_tmp")
                shutil.copy2(src, tmp)
                os.replace(tmp, dst)
            imported.append(name)
    except Exception as exc:
        # Immediate rollback of what existed before import.
        try:
            meta = json.loads((backup / "backup_manifest.json").read_text(encoding="utf-8"))
            existed = set(meta.get("existed", []))
            for name in imported:
                dst = DATA / name
                if name in existed and (backup / name).is_file():
                    shutil.copy2(backup / name, dst)
                elif name not in existed:
                    try:
                        dst.unlink()
                    except FileNotFoundError:
                        pass
        finally:
            write_status("import_failed_rolled_back", current_slug=current, error=str(exc), backup=str(backup))
        return 5

    marker = {
        "migration_state": "complete",
        "source_slug": manifest.get("source_slug", ""),
        "source_version": manifest.get("source_version", ""),
        "target_slug": current,
        "target_version": version,
        "source_fingerprint": fp,
        "backup": str(backup),
        "imported_files": imported,
        "completed_at": now_iso(),
    }
    atomic_json(IMPORT_MARKER, marker)
    atomic_json(COMPLETE, marker)
    write_status("import_complete", **marker)
    print(json.dumps({"result": "import_complete", **marker}, ensure_ascii=False))
    return 0


def rollback() -> int:
    if not IMPORT_MARKER.is_file():
        write_status("rollback_unavailable")
        return 1
    marker = json.loads(IMPORT_MARKER.read_text(encoding="utf-8"))
    backup = Path(str(marker.get("backup", "")))
    meta_path = backup / "backup_manifest.json"
    if not meta_path.is_file():
        write_status("rollback_backup_missing", backup=str(backup))
        return 2
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    existed = set(meta.get("existed", []))
    for name in MIGRATE_FILES:
        dst = DATA / name
        src = backup / name
        if name in existed and src.is_file():
            shutil.copy2(src, dst)
        elif name not in existed:
            try:
                dst.unlink()
            except FileNotFoundError:
                pass
    marker["rolled_back_at"] = now_iso()
    marker["migration_state"] = "rolled_back"
    atomic_json(IMPORT_MARKER, marker)
    try:
        COMPLETE.unlink()
    except FileNotFoundError:
        pass
    write_status("rollback_complete", backup=str(backup))
    return 0


def status() -> int:
    current = self_slug()
    out: dict[str, Any] = {"current_slug": current, "channel": channel(current), "handoff_ready": READY.exists(), "complete": COMPLETE.exists()}
    if STATUS.is_file():
        try:
            out["status"] = json.loads(STATUS.read_text(encoding="utf-8"))
        except Exception:
            pass
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def auto(version: str) -> int:
    current = self_slug()
    ch = channel(current)
    if ch == "local":
        return export_handoff(version)
    if ch == "store":
        return import_handoff(version)
    write_status("unknown_installation_channel", current_slug=current)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["auto", "export", "import", "rollback", "status"])
    ap.add_argument("--version", default=os.environ.get("SBC5CC_APP_VERSION", "unknown"))
    args = ap.parse_args()
    if args.command == "auto":
        return auto(args.version)
    if args.command == "export":
        return export_handoff(args.version)
    if args.command == "import":
        return import_handoff(args.version)
    if args.command == "rollback":
        return rollback()
    return status()


if __name__ == "__main__":
    raise SystemExit(main())
