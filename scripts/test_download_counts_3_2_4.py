#!/usr/bin/env python3
"""Offline failure-mode tests for GitHub Release ZIP counters and HA isolation.

Only reads app source; mocks the network. Never changes cooling, AI or hardware.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "custom_components/sbc5_control_center"
BRIDGE = ROOT / "local_apps/sbc5_control_center/bridge"
assert (NATIVE / "download_counts.py").read_bytes() == (BRIDGE / "download_counts.py").read_bytes()
spec = importlib.util.spec_from_file_location("sbc5_counter_regression", NATIVE / "download_counts.py")
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Missing ZIP does NOT mean zero people installed HACS.
assert module.count_release_assets("hacs", [{"assets": []}]) == (0, False)
# Genuine ZIP with zero downloads is numerically zero (and known).
assert module.count_release_assets("hacs", [{"assets": [
    {"id": 1, "name": "SBC5_Control_Center_Integration.zip", "download_count": 0}
]}]) == (0, True)
# We only count proper published release ZIPs; no drafts or checksums or field-test artifacts.
releases = [
    {"draft": True, "assets": [{"id": 2, "name": "SBC5_UPDATE_3.2.4.zip", "download_count": 500}]},
    {"draft": False, "assets": [
        {"id": 3, "name": "SBC5_UPDATE_3.2.4.zip", "download_count": 3},
        {"id": 3, "name": "SBC5_UPDATE_3.2.4.zip", "download_count": 3},
        {"id": 4, "name": "SBC5_UPDATE_3.2.4.zip.sha256", "download_count": 900},
        {"id": 5, "name": "SBC5_UPDATE_3.2.4_FIELD_TEST_CANDIDATE.zip", "download_count": 600},
    ]},
]
assert module.count_release_assets("app", releases) == (3, True)

# Paginated GitHub API results must include all pages before returning the total.
first_page = [{"assets": [{"id": 6, "name": "SBC5_UPDATE_3.2.3.zip", "download_count": 4}]}]
first_page.extend({"assets": []} for _ in range(99))
second_page = [{"assets": [{"id": 7, "name": "SBC5_UPDATE_3.2.4.zip", "download_count": 8}]}]
calls = []
class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def read(self, *_):
        return json.dumps(self.payload).encode("utf-8")
def fake_urlopen(request, timeout):
    calls.append((request.full_url, timeout))
    page = 2 if "page=2" in request.full_url else 1
    return FakeResponse(second_page if page == 2 else first_page)
with patch.object(module.urllib.request, "urlopen", side_effect=fake_urlopen):
    assert module._fetch_repo_downloads("app") == 12
assert len(calls) == 2, calls

# A partial GitHub outage must not spoof counts, and one repository's success
# must not be lost when the other one fails.
with patch.object(module, "_fetch_repo_downloads", side_effect=lambda source: 5 if source == "app" else (_ for _ in ()).throw(URLError("test offline"))):
    assert module.fetch_download_counts() == {"app": 5, "hacs": None}

# Public counts stay off the thermal-control hot path; GitHub is consulted
# through an executor and at most every six hours in the HA coordinator.
coordinator = (NATIVE / "coordinator.py").read_text(encoding="utf-8")
assert "async_add_executor_job(fetch_download_counts)" in coordinator
assert "time.monotonic() + 6 * 3600" in coordinator
assert '"app": None, "hacs": None' in coordinator
assert "release_downloads=dict(self._release_downloads)" in coordinator

print("SBC5 3.2.4 download counters offline failure-mode regression: PASS")
