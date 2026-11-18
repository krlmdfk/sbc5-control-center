#!/usr/bin/env python3
"""SBC5 3.3.0 read-only grouped diagnostics API and browser safety regressions."""
from __future__ import annotations
import ast
import io
import json
import os
from pathlib import Path
import re
import subprocess
from types import SimpleNamespace
from unittest.mock import patch

root = Path(__file__).resolve().parents[1] / "local_apps/sbc5_control_center"
code = (root / "config_ui.py").read_text(encoding="utf-8")
html = (root / "config_ui/index.html").read_text(encoding="utf-8")
javascript = (root / "config_ui/diagnostics.js").read_text(encoding="utf-8")

tree = ast.parse(code)
function = next(x for x in tree.body if isinstance(x, ast.FunctionDef)
                and x.name == "read_sbc5_sensor_states")
constants = {
    "SBC5_ENTITY_ID": re.compile(r"^(?:sensor|binary_sensor)\.sbc5_[a-z0-9_]{1,100}$"),
    "SBC5_DIAGNOSTICS_MAX_BYTES": 8 * 1024 * 1024,
    "SBC5_DIAGNOSTICS_MAX_ENTITIES": 600,
}
ns = {"os": os, "json": json, "re": re, **constants}
handler = type("Response", (io.BytesIO,), {"__enter__":lambda self:self,
                                        "__exit__":lambda self,*args:self.close()})
data = [
    {"entity_id":"sensor.sbc5_cpu_temperature", "state":"50.7",
     "attributes":{"friendly_name":"SBC5 CPU Temperature","unit_of_measurement":"°C","secret":"MUST_NOT_LEAK"}},
    {"entity_id":"binary_sensor.sbc5_ethernet_health","state":"on",
     "attributes":{"friendly_name":"Ethernet Health"}},
    {"entity_id":"sensor.other_integrations_secret","state":"supersecret",
     "attributes":{"friendly_name":"DO NOT SHARE"}},
    {"entity_id":"sensor.sbc5_invalid-hyphen","state":"123","attributes":{}},
]
captured = {}
def mock_open(req, timeout):
    captured["url"] = req.full_url
    captured["timeout"] = timeout
    captured["authorization"] = req.get_header("Authorization")
    return handler(json.dumps(data).encode("utf-8"))
ns["urllib"] = SimpleNamespace(request=SimpleNamespace(Request=lambda url,headers,method:
    SimpleNamespace(full_url=url, get_header=lambda k:headers.get(k)), urlopen=mock_open))
exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])),
             "config_ui.py", "exec"), ns)
with patch.dict(os.environ,{"SUPERVISOR_TOKEN":"INTERNAL_TOKEN_123"}):
    result = ns["read_sbc5_sensor_states"]()
assert captured["url"] == "http://supervisor/core/api/states"
assert captured["timeout"] == 5
assert captured["authorization"] == "Bearer INTERNAL_TOKEN_123"
assert result["count"] == 2
assert set(result["entities"][0]) == {"entity_id","name","state","unit"}
assert result["entities"][0]["unit"] == "°C"
assert "INTERNAL_TOKEN_123" not in json.dumps(result)
assert "MUST_NOT_LEAK" not in json.dumps(result)
assert "supersecret" not in json.dumps(result)
assert "api/diagnostics/entities" in code
assert "if not self._require_ingress_peer(): return" in code
assert "SBC5_DIAGNOSTICS_MAX_BYTES + 1" in code
assert "if len(selected) >= SBC5_DIAGNOSTICS_MAX_ENTITIES:" in code
assert "diagnostics.js" in html and "sbc5DiagnosticsTab" in html
assert "sbc5ConfigTab" in html and 'role="tablist"' in html
assert "document.createElement" in javascript
assert ".textContent" in javascript
assert "innerHTML" not in javascript
assert "eval(" not in javascript
assert "localStorage" not in javascript
assert "api/diagnostics/entities" in javascript
assert "setInterval" in javascript
assert "diagnostics" in javascript and "configuration" in javascript
assert "sbc5-diag-group-name" in javascript
assert "window.setInterval" in javascript
# This view must never call a state-changing HA service or option-save route.
assert "api/save" not in javascript
assert "callService(" not in javascript
assert "callWS(" not in javascript
assert "SUPERVISOR_TOKEN" not in javascript
# JS syntax is verified by Node present on the GitHub ubuntu-latest CI image.
check=subprocess.run(["node","--check",str(root/"config_ui/diagnostics.js")],
                    text=True,capture_output=True,timeout=10)
assert check.returncode == 0, check.stderr
print("SBC5 3.3.0 grouped read-only diagnostics, boundary, browser syntax: PASS")
