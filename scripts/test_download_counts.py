#!/usr/bin/env python3
"""Offline regression for optional GitHub Release ZIP download counters."""
from __future__ import annotations
import importlib.util
import io
import json
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "custom_components/sbc5_control_center/download_counts.py"
BRIDGE = ROOT / "local_apps/sbc5_control_center/bridge/download_counts.py"
assert CANON.read_bytes() == BRIDGE.read_bytes(), "App and bundled bridge must be identical"
spec = importlib.util.spec_from_file_location("sbc5_download_counts", CANON)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

releases = [
    {"draft": True, "assets": [{"id": 1, "name": "SBC5_UPDATE_3.2.2.zip", "download_count": 900}]},
    {"draft": False, "assets": [
        {"id": 2, "name": "SBC5_UPDATE_3.2.2.zip", "download_count": 7},
        {"id": 3, "name": "SBC5_UPDATE_3.2.2.zip.sha256", "download_count": 900},
        {"id": 4, "name": "SBC5_UPDATE_3.2.2_FIELD_TEST_CANDIDATE.zip", "download_count": 400},
    ]},
]
assert mod.count_release_assets("app", releases) == (7, True)
assert mod.count_release_assets("hacs", releases) == (0, False)
assert mod.count_release_assets("hacs", [{"assets": [{"id": 8, "name": "SBC5_Control_Center_Integration.zip", "download_count": 3}]}]) == (3, True)

class FakeResponse:
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def read(self, *_): return json.dumps(releases).encode()

with patch.object(mod.urllib.request, "urlopen", return_value=FakeResponse()) as fetch:
    assert mod._fetch_repo_downloads("app") == 7
    assert fetch.call_count == 1
with patch.object(mod.urllib.request, "urlopen", return_value=FakeResponse()):
    assert mod._fetch_repo_downloads("hacs") is None

print("SBC5 release download counters: PASS")
