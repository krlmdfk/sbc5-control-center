#!/usr/bin/env python3
"""Read-only regression for raw/stabilized forecast observability.

This test must not write to PWM, reset AI learning, or alter predictor authority.
"""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
runtime = (APP / "ai_cooling_v5_2.py").read_text(encoding="utf-8")
policy_file = APP / "thermal_active_policy.py"

spec = importlib.util.spec_from_file_location("thermal_policy_observability", policy_file)
assert spec and spec.loader
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)

state = {}
for raw in (51.0, 51.0, 51.0):
    policy.stabilize_forecast(
        state, raw_forecast=raw, target=49.0,
        confidence=90.0, average_mae=1.0,
    )
before = policy.stabilize_forecast(
    state, raw_forecast=48.8, target=49.0,
    confidence=77.0, average_mae=1.6,
)
assert before["stable_forecast_c"] > 49.0
assert before["stable_forecast_c"] - 48.8 >= 1.0
assert before["hot_confirm_cycles"] >= 1

# Raw/conditioned values and their signed difference are available in status.
assert '"weighted_forecast_raw_c": round(raw_weighted, 2)' in runtime
assert '"forecast_filter_lag_c": filter_lag' in runtime
assert '"forecast_filter_lag_significant": abs(filter_lag) >= 1.0' in runtime
assert '"forecast_filter_lag_c": guidance.get("forecast_filter_lag_c")' in runtime
assert '"forecast_filter_lag_significant": guidance.get("forecast_filter_lag_significant", False)' in runtime

# The TSV contract is append-only. Existing legacy positional indices 22:39 remain.
tree = ast.parse(runtime)
apply = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_apply_guided_step")
diagnostics = next(n for n in ast.walk(apply)
                   if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "diagnostic_fields" for t in n.targets))
assert isinstance(diagnostics.value, ast.List)
assert len(diagnostics.value.elts) == 19
assert 'fields[22:41] = diagnostic_fields' in runtime
assert 'if len(fields) < 39:' in runtime

# The built container applies the Setpoint Stability patch after earlier patches.
# Its runtime log must expose both fields without moving old TSV columns.
legacy = (APP / "run_legacy.sh").read_text(encoding="utf-8")
patch32 = (APP / "patch_setpoint_stability_3_1_32.py").read_text(encoding="utf-8")
assert "tp_decision_reason tp_weighted_raw tp_filter_lag <<<" in legacy
assert 'tp_weighted_raw="" tp_filter_lag=""' in legacy
assert 'raw_weighted=${tp_weighted_raw}C filter_lag=${tp_filter_lag}C' in patch32

# No new control authority or change to emergency limits.
assert policy.ACTIVE_MAX_DELTA_PP == 2
assert policy.PROBATION_MAX_DELTA_PP == 1
assert 'guided_output = int(round(policy.clamp(output + requested_delta, lo, hi)))' in runtime
assert 'status["output_pwm_percent"] = guided_output' in runtime
print("SBC5 Thermal Predictor raw/filtered observability: PASS")
