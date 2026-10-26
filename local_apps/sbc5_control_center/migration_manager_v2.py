#!/usr/bin/env python3
"""SBC5 durable-state migration manager.

Supports two safe handoff modes:
- replace: legacy local-App -> Store migration where the source is superseded;
- canary_test: Store stable -> newer Store/canary test instance without deprecating
  or modifying the stable source. This is used to validate a future in-place release
  with real user state before that release is published on the stable repository.

The manager never reads another App's private /data. The source exports only an
allow-list to the shared Home Assistant config tree. The target validates the exact
slug, version (when available), file allow-list and SHA-256 fingerprint before import.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
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
CANARY_COMPLETE = HANDOFF / "CANARY_COMPLETE.json"
STATUS = DATA / "store_migration_status.json"
IMPORT_MARKER = DATA / "store_migration_import.json"
BACKUP_ROOT = DATA / "migration_backups"
PROFILE_SYNC_MARKER = DATA / "profile_supervisor_sync_state.json"
PROFILE_MIGRATION_GUARD = DATA / "store_migration_profile_guard.json"

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

RUNNING_STATES = {"started", "running"}


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def semver(value: str) -> tuple[int, int, int] | None:
    try:
        parts = value.strip().split(".")
        if len(parts) != 3:
            return None
        parsed = tuple(int(x) for x in parts)
        if any(x < 0 for x in parsed):
            return None
        return parsed  # type: ignore[return-value]
    except (AttributeError, TypeError, ValueError):
        return None


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
    for app in installed_apps():
        if str(app.get("name", "")) == "SBC5 Control Center" and str(app.get("state", "")) in RUNNING_STATES:
            return str(app.get("slug", ""))
    return "local_sbc5_control_center"


def channel(slug: str) -> str:
    if slug.startswith("local_"):
        return "local"
    if slug.endswith("_sbc5_control_center"):
        return "store"
    return "unknown"


def app_version(app: dict[str, Any]) -> str:
    for key in ("version", "version_latest"):
        value = app.get(key)
        if value:
            return str(value)
    return ""


def app_by_slug(slug: str) -> dict[str, Any] | None:
    for app in installed_apps():
        if str(app.get("slug", "")) == slug:
            return app
    return None


def app_state(slug: str) -> str:
    app = app_by_slug(slug)
    return str(app.get("state", "")) if app else ""


def select_target(current: str, source_version: str) -> tuple[str, str, str]:
    """Return target slug, target version and handoff mode."""
    source_channel = channel(current)
    candidates: list[tuple[tuple[int, int, int], str, str, bool]] = []
    source_semver = semver(source_version)

    for app in installed_apps():
        slug = str(app.get("slug", ""))
        if slug == current or channel(slug) != "store" or not app.get("installed", True):
            continue
        version = app_version(app)
        parsed = semver(version)
        if parsed is None:
            continue
        if source_channel == "store" and (source_semver is None or parsed <= source_semver):
            continue
        stopped = str(app.get("state", "")) not in RUNNING_STATES
        candidates.append((parsed, slug, version, stopped))

    if not candidates:
        return "", "", ""

    # Prefer a stopped target, then the newest version.
    candidates.sort(key=lambda x: (x[3], x[0]), reverse=True)
    _, slug, version, _ = candidates[0]
    return slug, version, "canary_test" if source_channel == "store" else "replace"


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


def load_manifest_header() -> dict[str, Any]:
    if not MANIFEST.is_file():
        return {}
    try:
        value = json.loads(MANIFEST.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def export_handoff(version: str) -> int:
    current = self_slug()
    source_channel = channel(current)
    if source_channel not in {"local", "store"}:
        write_status("export_skipped_unknown_channel", current_slug=current)
        return 0

    # Only a replacement migration deprecates its source. A canary test never does.
    if source_channel == "local" and COMPLETE.exists():
        try:
            done = json.loads(COMPLETE.read_text(encoding="utf-8"))
        except Exception:
            done = {}
        if done.get("source_slug") == current and done.get("mode", "replace") == "replace":
            write_status("source_deprecated_after_store_migration", current_slug=current, target_slug=done.get("target_slug", ""))
            return 21

    target, target_version, mode = select_target(current, version)
    if not target:
        state = "export_skipped_no_newer_store_target" if source_channel == "store" else "export_skipped_no_store_target"
        write_status(state, current_slug=current, source_version=version)
        return 0
    if app_state(target) in RUNNING_STATES:
        write_status("export_blocked_store_running", current_slug=current, target_slug=target, target_version=target_version, mode=mode)
        return 22

    SHARED_PARENT.mkdir(parents=True, exist_ok=True)
    tmp = SHARED_PARENT / f".store_handoff_v1.tmp.{os.getpid()}"
    shutil.rmtree(tmp, ignore_errors=True)
    (tmp / "payload").mkdir(parents=True)
    hashes = collect_payload(DATA, tmp / "payload")
    if not hashes:
        shutil.rmtree(tmp, ignore_errors=True)
        write_status("export_failed_empty", current_slug=current, target_slug=target, mode=mode)
        return 3

    manifest = {
        "schema": 2,
        "mode": mode,
        "source_slug": current,
        "source_channel": source_channel,
        "source_version": version,
        "target_slug": target,
        "target_version": target_version,
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
    if not isinstance(manifest, dict) or manifest.get("schema") not in {1, 2}:
        raise RuntimeError("unsupported_schema")
    target = str(manifest.get("target_slug", ""))
    if target and target != current:
        raise RuntimeError(f"wrong_target:{target}")
    mode = str(manifest.get("mode", "replace"))
    if mode not in {"replace", "canary_test"}:
        raise RuntimeError(f"unsupported_mode:{mode}")
    source = str(manifest.get("source_slug", ""))
    if not source or source == current:
        raise RuntimeError("invalid_source")
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


def write_profile_migration_guard(source_fingerprint: str, source_slug: str, target_slug: str, mode: str) -> None:
    try:
        PROFILE_SYNC_MARKER.unlink()
    except FileNotFoundError:
        pass
    atomic_json(
        PROFILE_MIGRATION_GUARD,
        {
            "state": "pending",
            "mode": mode,
            "source_fingerprint": source_fingerprint,
            "source_slug": source_slug,
            "target_slug": target_slug,
            "created_at": now_iso(),
        },
    )


def import_handoff(version: str) -> int:
    current = self_slug()
    if channel(current) != "store":
        write_status("import_skipped_not_store", current_slug=current)
        return 0
    if not READY.exists():
        write_status("import_skipped_no_handoff", current_slug=current)
        return 0

    header = load_manifest_header()
    target = str(header.get("target_slug", ""))
    if target and target != current:
        # A stale/foreign handoff must never be reported as a failed import and must
        # never initialize this instance from another target's data.
        write_status("import_skipped_foreign_handoff", current_slug=current, handoff_target=target, handoff_source=header.get("source_slug", ""))
        return 0

    if IMPORT_MARKER.exists():
        try:
            marker = json.loads(IMPORT_MARKER.read_text(encoding="utf-8"))
            if marker.get("source_fingerprint") and marker.get("source_fingerprint") == header.get("fingerprint"):
                write_status("import_already_complete", current_slug=current, **marker)
                return 0
        except Exception:
            pass

    source_slug = str(header.get("source_slug", ""))
    mode = str(header.get("mode", "replace"))
    source_app = app_by_slug(source_slug) if source_slug else None
    source_state = str(source_app.get("state", "")) if source_app else ""

    # For a canary test, the stable source must still exist for an immediate rollback
    # and it must be stopped before the canary is allowed to become authoritative.
    if mode == "canary_test" and not source_app:
        write_status("import_waiting_source_present", current_slug=current, source_slug=source_slug, mode=mode)
        return 20
    if source_state in RUNNING_STATES:
        write_status("import_waiting_source_stop", current_slug=current, source_slug=source_slug, source_state=source_state, mode=mode)
        return 20

    try:
        manifest, fp = verify_handoff(current)
    except Exception as exc:
        write_status("import_verification_failed", current_slug=current, error=str(exc), mode=mode)
        # A handoff explicitly targeted at this canary must fail closed: run.sh already
        # treats rc=20 as a pre-controller wait state.
        return 20 if mode == "canary_test" else 4

    expected_target_version = str(manifest.get("target_version", ""))
    if expected_target_version and semver(expected_target_version) and semver(version) and semver(expected_target_version) != semver(version):
        write_status(
            "import_waiting_target_version",
            current_slug=current,
            running_version=version,
            expected_target_version=expected_target_version,
            mode=mode,
        )
        return 20 if mode == "canary_test" else 4

    names = sorted(str(x) for x in manifest["files"])
    backup_names = sorted(set(names + [PROFILE_SYNC_MARKER.name, PROFILE_MIGRATION_GUARD.name]))
    backup = backup_current(backup_names, fp)
    imported: list[str] = []
    try:
        for name in names:
            src = PAYLOAD / name
            dst = DATA / name
            if name == "options.json":
                try:
                    current_options = json.loads(dst.read_text(encoding="utf-8")) if dst.is_file() else {}
                    source_options = json.loads(src.read_text(encoding="utf-8"))
                    atomic_json(dst, deep_merge(current_options, source_options))
                except Exception:
                    shutil.copy2(src, dst)
            else:
                tmp = DATA / (name + ".migration_tmp")
                shutil.copy2(src, tmp)
                os.replace(tmp, dst)
            imported.append(name)
    except Exception as exc:
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
            write_status("import_failed_rolled_back", current_slug=current, error=str(exc), backup=str(backup), mode=mode)
        return 20 if mode == "canary_test" else 5

    write_profile_migration_guard(fp, str(manifest.get("source_slug", "")), current, mode)
    marker = {
        "migration_state": "complete",
        "mode": mode,
        "source_slug": manifest.get("source_slug", ""),
        "source_version": manifest.get("source_version", ""),
        "target_slug": current,
        "target_version": version,
        "source_fingerprint": fp,
        "backup": str(backup),
        "imported_files": imported,
        "profile_sync_guard": "pending",
        "completed_at": now_iso(),
    }
    atomic_json(IMPORT_MARKER, marker)
    if mode == "replace":
        atomic_json(COMPLETE, marker)
    else:
        atomic_json(CANARY_COMPLETE, marker)
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
    rollback_files = tuple(MIGRATE_FILES) + (PROFILE_SYNC_MARKER.name, PROFILE_MIGRATION_GUARD.name)
    for name in rollback_files:
        dst = DATA / name
        src = backup / name
        if name in existed and src.is_file():
            shutil.copy2(src, dst)
        elif name not in existed:
            try:
                dst.unlink()
            except FileNotFoundError:
                pass
    try:
        IMPORT_MARKER.unlink()
    except FileNotFoundError:
        pass
    if marker.get("mode") == "canary_test":
        try:
            CANARY_COMPLETE.unlink()
        except FileNotFoundError:
            pass
    write_status("rollback_complete", backup=str(backup), mode=marker.get("mode", "replace"))
    return 0


def status() -> int:
    current = self_slug()
    out: dict[str, Any] = {
        "current_slug": current,
        "channel": channel(current),
        "handoff_ready": READY.exists(),
        "complete": COMPLETE.exists(),
        "canary_complete": CANARY_COMPLETE.exists(),
    }
    for key, path in (("status", STATUS), ("manifest", MANIFEST), ("import", IMPORT_MARKER)):
        if path.is_file():
            try:
                out[key] = json.loads(path.read_text(encoding="utf-8"))
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
