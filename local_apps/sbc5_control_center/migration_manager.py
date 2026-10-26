#!/usr/bin/env python3
"""SBC5 migration entrypoint.

The implementation lives in migration_manager_v2.py. This entrypoint owns the
runtime routing decision so a stable Store instance exports to a newer stopped
canary, while a canary imports only a handoff explicitly targeted at its own slug.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import migration_manager_v2 as impl


def auto(version: str) -> int:
    current = impl.self_slug()
    ch = impl.channel(current)

    if ch == "local":
        return impl.export_handoff(version)

    if ch == "store":
        # If a shared handoff explicitly targets this Store identity, this
        # instance is the target and must import (or wait fail-closed).
        header = impl.load_manifest_header()
        if impl.READY.exists() and str(header.get("target_slug", "")) == current:
            return impl.import_handoff(version)

        # Otherwise a stable Store instance may act as the source for a newer,
        # already installed and stopped canary. Export is read-only with respect
        # to the source /data and never deprecates the stable instance.
        target, _target_version, mode = impl.select_target(current, version)
        if target and mode == "canary_test":
            return impl.export_handoff(version)

        # No newer target. This also handles a stale/foreign handoff safely:
        # import_handoff() ignores a handoff addressed to another slug.
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
