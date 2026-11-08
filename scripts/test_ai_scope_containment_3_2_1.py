#!/usr/bin/env python3
"""Static safety contract: AI modules cannot gain unrelated capabilities accidentally.

This is defense-in-depth, not a container escape or malicious-root-app guarantee.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps/sbc5_control_center"
AI_MODULES = (
    "ai_cooling_legacy.py",
    "ai_cooling.py",
    "ai_cooling_v5.py",
    "ai_cooling_v5_1.py",
    "ai_cooling_v5_2.py",
    "thermal_predictor_v3.py",
    "thermal_active_policy.py",
    "thermal_effectiveness.py",
)
# A new network client, shell executor or plugin loader requires explicit
# independent security review, not just a green CI run.
PROHIBITED_IMPORT_ROOTS = {
    "subprocess", "socket", "socketserver", "requests", "urllib",
    "http", "ftplib", "telnetlib", "smtplib", "asyncio",
    "multiprocessing", "ctypes", "cffi", "paramiko", "pexpect",
}
PROHIBITED_CALLS = {"eval", "exec", "__import__"}
for file in AI_MODULES:
    code = (APP / file).read_text(encoding="utf-8")
    tree = ast.parse(code, filename=file)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                assert name.name.split(".")[0] not in PROHIBITED_IMPORT_ROOTS, (file, name.name)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in PROHIBITED_IMPORT_ROOTS, (file, node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in PROHIBITED_CALLS, (file, node.func.id)
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {"system", "popen", "spawn", "fork", "execv",
                                              "execve", "startfile"}, (file, node.func.attr)

legacy = (APP / "run_legacy.sh").read_text(encoding="utf-8")
assert 'AI_COOLING_MODEL_FILE="/data/ai_cooling_model.json"' in legacy
assert 'AI_COOLING_STATUS_FILE="/data/ai_cooling_status.json"' in legacy
assert 'AI_COOLING_MIRROR_FILE="/homeassistant/sbc5_control_center/ai_cooling.json"' in legacy
assert 'AI_COOLING_SCRIPT="/ai_cooling.py"' in legacy
assert '--model "$AI_COOLING_MODEL_FILE" --status "$AI_COOLING_STATUS_FILE"' in legacy
assert '--telemetry "$TELEMETRY_STATE_FILE"' in legacy

# AI produces a scalar request: only the separate adaptive controller writes fan
# hardware. Keep explicit actuator and override limits in the call chain.
controller_start = legacy.index('adaptive_pwm_controller_loop() {')
controller_end = legacy.index('\ntelemetry_publisher_loop() {', controller_start)
controller = legacy[controller_start:controller_end]
assert 'ai_result="$(python3 "$AI_COOLING_SCRIPT" step' in controller
assert 'IFS=$\'\\t\' read -r ai_output' in controller
assert 'if [ "$action" != "safety_max" ]; then' in controller
assert 'final_low=$((curve_state - adaptive_trim_limit - AI_COOLING_ASSIST_LIMIT_PCT))' in controller
assert 'final_high=$((curve_state + adaptive_trim_limit + AI_COOLING_ASSIST_LIMIT_PCT))' in controller
assert 'if [ "$desired" -gt $((controller_state + step_up)) ]' in controller
assert 'owner_now="$(jq -r' in controller
assert '"$owner_now" != "adaptive"' in controller
assert 'printf \'%s\\n\' "$desired" > "$dev/cur_state"' in controller
for name in AI_MODULES:
    body = (APP / name).read_text(encoding="utf-8")
    assert 'cur_state' not in body, f"AI module accesses fan actuator: {name}"

# The predictor owns no separate scheduler, shell commands or independent fan writes.
guided = (APP / "ai_cooling_v5_2.py").read_text(encoding="utf-8")
assert '"mode")) == "assist" and requested_delta' in guided
assert 'policy.clamp(output + requested_delta, lo, hi)' in guided

print("SBC5 AI static capability and actuator boundary audit: PASS")
