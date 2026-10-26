#!/usr/bin/env python3
"""SBC5 migration entrypoint.

The implementation lives in migration_manager_v2.py. This entrypoint owns the
runtime routing decision so a stable Store instance exports to a newer stopped
canary, while a canary imports only a handoff explicitly targeted at its own slug.

A completed legacy handoff addressed to the current Store identity must not keep
blocking future canary exports. When the current /data already contains a matching
completed import marker, the old READY/manifest pair is treated as historical for
routing purposes; its backup and audit files are left untouched.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import migration_manager_v2 as impl


def _completed_handoff_matches_current_import(header: dict) -> bool:
    """Return True only for a handoff already imported into this exact instance."""
    if not impl.IMPORT_MARKER.is_file():
        return False
    try:
        marker = json.loads(impl.IMPORT_MARKER.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(marker, dict):
        return False
    header_fp = str(header.get("fingerprint", ""))
    marker_fp = str(marker.get("source_fingerprint", ""))
    return bool(
        header_fp
        and marker_fp == header_fp
        and str(marker.get("migration_state", "")) == "complete"
        and str(marker.get("target_slug", "")) == impl.self_slug()
    )


def auto(version: str) -> int:
    current = impl.self_slug()
    ch = impl.channel(current)

    if ch == "local":
        return impl.export_handoff(version)

    if ch == "store":
        header = impl.load_manifest_header()
        addressed_here = impl.READY.exists() and str(header.get("target_slug", "")) == current

        # A handoff that is addressed to this Store identity and has not yet been
        # imported remains authoritative and must be imported (or wait fail-closed).
        # If the exact fingerprint is already marked complete in this /data, it is
        # historical and must not prevent this stable Store instance from exporting
        # a fresh state snapshot to a newer stopped canary.
        if addressed_here and not _completed_handoff_matches_current_import(header):
            return impl.import_handoff(version)

        target, _target_version, mode = impl.select_target(current, version)
        if target and mode == "canary_test":
            return impl.export_handoff(version)

        # No newer target exists. Preserve the old audit state and let the normal
        # importer report import_already_complete / foreign_handoff / no_handoff.
        return impl.import_handoff(version)

    impl.write_status("unknown_installation_channel", current_slug=current)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["auto", "export", "import", "rollback", "status"])
    ap.add_argument("--version", default=os.environ.get("SBC5CC_APP_VERSION", "unknown"))
    args = ap.parse_args()

    if args.command == "auto":
        return auto(args.version)
    if args.command == "export":
        return impl.export_handoff(args.version)
    if args.command == "import":
        return impl.import_handoff(args.version)
    if args.command == "rollback":
        return impl.rollback()
    return impl.status()


if __name__ == "__main__":
    raise SystemExit(main())
