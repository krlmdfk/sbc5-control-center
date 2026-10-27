#!/usr/bin/env python3
"""Regression tests for SBC5 stable-Store -> Rust canary state handoff."""
from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
sys.path.insert(0, str(APP))

impl = importlib.import_module("migration_manager_v2")
entry = importlib.import_module("migration_manager")


def apps(stable_state="started", canary_state="stopped"):
    return [
        {
            "slug": "aaaa_stable_sbc5_control_center",
            "name": "SBC5 Control Center",
            "version": "2.8.32",
            "state": stable_state,
            "installed": True,
        },
        {
            "slug": "bbbb_canary_sbc5_control_center",
            "name": "SBC5 Control Center",
            "version": "3.0.0",
            "state": canary_state,
            "installed": True,
        },
    ]


def test_target_selection():
    old = impl.installed_apps
    try:
        impl.installed_apps = lambda: apps()
        target, version, mode = impl.select_target("aaaa_stable_sbc5_control_center", "2.8.32")
        assert target == "bbbb_canary_sbc5_control_center"
        assert version == "3.0.0"
        assert mode == "canary_test"
    finally:
        impl.installed_apps = old


def test_entrypoint_routes_stable_to_export():
    old_self, old_channel = impl.self_slug, impl.channel
    old_load, old_select = impl.load_manifest_header, impl.select_target
    old_export, old_import, old_ready = impl.export_handoff, impl.import_handoff, impl.READY
    calls = []

    class MissingReady:
        @staticmethod
        def exists():
            return False

    try:
        impl.self_slug = lambda: "aaaa_stable_sbc5_control_center"
        impl.channel = lambda _slug: "store"
        impl.READY = MissingReady()
        impl.load_manifest_header = lambda: {}
        impl.select_target = lambda _slug, _version: ("bbbb_canary_sbc5_control_center", "3.0.0", "canary_test")
        impl.export_handoff = lambda version: calls.append(("export", version)) or 0
        impl.import_handoff = lambda version: calls.append(("import", version)) or 0
        assert entry.auto("2.8.32") == 0
        assert calls == [("export", "2.8.32")]
    finally:
        impl.self_slug, impl.channel = old_self, old_channel
        impl.load_manifest_header, impl.select_target = old_load, old_select
        impl.export_handoff, impl.import_handoff, impl.READY = old_export, old_import, old_ready


def test_entrypoint_routes_target_to_import():
    old_self, old_channel = impl.self_slug, impl.channel
    old_load, old_import, old_ready = impl.load_manifest_header, impl.import_handoff, impl.READY
    calls = []

    class Ready:
        @staticmethod
        def exists():
            return True

    try:
        impl.self_slug = lambda: "bbbb_canary_sbc5_control_center"
        impl.channel = lambda _slug: "store"
        impl.READY = Ready()
        impl.load_manifest_header = lambda: {"target_slug": "bbbb_canary_sbc5_control_center"}
        impl.import_handoff = lambda version: calls.append(("import", version)) or 0
        assert entry.auto("3.0.0") == 0
        assert calls == [("import", "3.0.0")]
    finally:
        impl.self_slug, impl.channel = old_self, old_channel
        impl.load_manifest_header, impl.import_handoff, impl.READY = old_load, old_import, old_ready


def test_foreign_handoff_is_ignored_and_source_running_waits():
    old_values = {
        "DATA": impl.DATA,
        "SHARED_PARENT": impl.SHARED_PARENT,
        "HANDOFF": impl.HANDOFF,
        "READY": impl.READY,
        "MANIFEST": impl.MANIFEST,
        "PAYLOAD": impl.PAYLOAD,
        "COMPLETE": impl.COMPLETE,
        "CANARY_COMPLETE": impl.CANARY_COMPLETE,
        "STATUS": impl.STATUS,
        "IMPORT_MARKER": impl.IMPORT_MARKER,
        "BACKUP_ROOT": impl.BACKUP_ROOT,
        "PROFILE_SYNC_MARKER": impl.PROFILE_SYNC_MARKER,
        "PROFILE_MIGRATION_GUARD": impl.PROFILE_MIGRATION_GUARD,
        "self_slug": impl.self_slug,
        "channel": impl.channel,
        "installed_apps": impl.installed_apps,
    }
    try:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data = root / "data"
            shared = root / "shared"
            handoff = shared / "store_handoff_v1"
            payload = handoff / "payload"
            data.mkdir()
            payload.mkdir(parents=True)
            (handoff / "READY").write_text("x\n")

            impl.DATA = data
            impl.SHARED_PARENT = shared
            impl.HANDOFF = handoff
            impl.READY = handoff / "READY"
            impl.MANIFEST = handoff / "manifest.json"
            impl.PAYLOAD = payload
            impl.COMPLETE = handoff / "COMPLETE.json"
            impl.CANARY_COMPLETE = handoff / "CANARY_COMPLETE.json"
            impl.STATUS = data / "status.json"
            impl.IMPORT_MARKER = data / "import.json"
            impl.BACKUP_ROOT = data / "backups"
            impl.PROFILE_SYNC_MARKER = data / "profile_sync.json"
            impl.PROFILE_MIGRATION_GUARD = data / "profile_guard.json"
            impl.self_slug = lambda: "bbbb_canary_sbc5_control_center"
            impl.channel = lambda _slug: "store"

            impl.MANIFEST.write_text(json.dumps({
                "schema": 2,
                "mode": "canary_test",
                "source_slug": "aaaa_stable_sbc5_control_center",
                "target_slug": "cccc_other_sbc5_control_center",
                "files": {"options.json": "deadbeef"},
                "fingerprint": "bad",
            }))
            assert impl.import_handoff("3.0.0") == 0
            status = json.loads(impl.STATUS.read_text())
            assert status["state"] == "import_skipped_foreign_handoff"
            assert not impl.IMPORT_MARKER.exists()

            impl.MANIFEST.write_text(json.dumps({
                "schema": 2,
                "mode": "canary_test",
                "source_slug": "aaaa_stable_sbc5_control_center",
                "source_version": "2.8.32",
                "target_slug": "bbbb_canary_sbc5_control_center",
                "target_version": "3.0.0",
                "files": {"options.json": "deadbeef"},
                "fingerprint": "bad",
            }))
            impl.installed_apps = lambda: apps(stable_state="started", canary_state="started")
            assert impl.import_handoff("3.0.0") == 20
            status = json.loads(impl.STATUS.read_text())
            assert status["state"] == "import_waiting_source_stop"
    finally:
        for name, value in old_values.items():
            setattr(impl, name, value)


def main():
    test_target_selection()
    test_entrypoint_routes_stable_to_export()
    test_entrypoint_routes_target_to_import()
    test_foreign_handoff_is_ignored_and_source_running_waits()
    print("PASS: canary migration routing and fail-closed guards")


if __name__ == "__main__":
    main()
