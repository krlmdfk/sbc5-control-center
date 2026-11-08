#!/usr/bin/env python3
"""Standalone tests of SBC5 Ingress JSON request boundaries.

Extracts the production parser and numeric validator to avoid importing a live
application module or starting the privileged configuration server in CI.
"""
from __future__ import annotations

import ast
from io import BytesIO
import math
from pathlib import Path
from types import SimpleNamespace
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "local_apps/sbc5_control_center/config_ui.py"
text = SOURCE.read_text(encoding="utf-8")
tree = ast.parse(text)
find = lambda name: next(n for n in tree.body if getattr(n, "name", None) == name)
handler = find("H")
parser = next(n for n in handler.body if getattr(n, "name", None) == "_read_json_request")
error_cls = find("JsonRequestError")
clamp = find("clamp_num")
ns = {"json": json, "re": re, "math": math, "MAX_POST_BYTES": 8 * 1024 * 1024}
module = ast.Module(body=[error_cls, clamp], type_ignores=[])
exec(compile(ast.fix_missing_locations(module), str(SOURCE), "exec"), ns)
parser_class = ast.ClassDef(name="Parser", bases=[], keywords=[], body=[parser], decorator_list=[])
exec(compile(ast.fix_missing_locations(ast.Module(body=[parser_class], type_ignores=[])), str(SOURCE), "exec"), ns)
Parser, JsonRequestError, clamp_num = ns["Parser"], ns["JsonRequestError"], ns["clamp_num"]


def request(raw: bytes, headers: dict[str, str] | None = None):
    p = Parser()
    p.rfile = BytesIO(raw)
    p.headers = {
        "Content-Type": "application/json",
        "Content-Length": str(len(raw)),
        **(headers or {}),
    }
    return p


def expect_bad(raw: bytes, headers: dict[str, str] | None = None, code: int = 400):
    p = request(raw, headers)
    try:
        p._read_json_request()
    except JsonRequestError as err:
        assert err.status == code, (err.status, code, str(err))
    else:
        raise AssertionError(f"invalid request accepted: {headers!r} {raw[:80]!r}")


assert request(b'{"confirm":true}')._read_json_request() == {"confirm": True}
assert request(b'{"options":{"custom_target_temp_c":49}}', {"Content-Type": "application/json; charset=utf-8"})._read_json_request()["options"]["custom_target_temp_c"] == 49
expect_bad(b"{}", {"Content-Type": "text/plain"}, 415)
expect_bad(b"{}", {"Content-Length": "-1"})
expect_bad(b"{}", {"Content-Length": "invalid"})
expect_bad(b"{}", {"Content-Length": str(8 * 1024 * 1024 + 1)}, 413)
expect_bad(b"{}", {"Content-Length": "10"})
expect_bad(b"{}", {"Content-Length": ""})
expect_bad(b"{}", {"Content-Length": "0"})
expect_bad(b"{}", {"Transfer-Encoding": "chunked"})
expect_bad(b"{} invalid")
expect_bad(b"[]")
expect_bad(b"null")
expect_bad(b"123")
expect_bad(b'"string"')
expect_bad(b"")
expect_bad(b"{}", {"Content-Length": "99999999999"})
assert clamp_num("49", 46, 65) == 49.0
for bad in ("nan", "NaN", "inf", "-inf", float("nan"), float("inf")):
    try:
        clamp_num(bad, 46, 65)
    except ValueError:
        continue
    raise AssertionError(f"accepted nonfinite numeric setting: {bad!r}")

# Regression: documented protocol boundary must precede all mutable actions.
assert "payload = self._read_json_request()" in text
assert text.index("payload = self._read_json_request()") < text.index("if self.path=='/api/save'")
assert "ThreadingHTTPServer(('0.0.0.0',PORT),H).serve_forever()" in text  # no routing change
print("SBC5 Ingress JSON request bounds and finite numeric validation: PASS")
