#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "local_apps/sbc5_control_center/ai_cooling_v5_1.py"
spec = importlib.util.spec_from_file_location("ai_v5_1_direct_diag_test", path)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Sparse bucket: direct diagnostics must remain 0/none even when effective/global
# confidence is already non-zero thanks to transfer/transient evidence.
status = {
    "bin_qualified_samples": 0,
    "direct_confidence_percent": 45,
    "direct_prediction_pwm_percent": 83,
    "direct_model_maturity_percent": 45,
    "direct_blend_percent": 35,
    "global_confidence_percent": 34,
    "effective_confidence_percent": 45,
    "transient_confidence_percent": 18,
}
fields = ["0"] * 22
fields[14] = "45"
fields[17] = "83"
mod._normalize_direct_diagnostics(status, fields)
assert status["direct_confidence_percent"] == 0
assert status["direct_prediction_pwm_percent"] is None
assert status["direct_model_maturity_percent"] == 0
assert status["direct_blend_percent"] == 0
assert fields[14] == "0"
assert fields[17] == "-1"
# Transfer/effective diagnostics are intentionally untouched.
assert status["global_confidence_percent"] == 34
assert status["effective_confidence_percent"] == 45
assert status["transient_confidence_percent"] == 18

# Mature/qualified bucket: direct diagnostics must pass through unchanged.
status2 = {
    "bin_qualified_samples": 5,
    "direct_confidence_percent": 17,
    "direct_prediction_pwm_percent": 42,
    "direct_model_maturity_percent": 17,
    "direct_blend_percent": 13,
}
fields2 = ["0"] * 22
fields2[14] = "17"
fields2[17] = "42"
mod._normalize_direct_diagnostics(status2, fields2)
assert status2["direct_confidence_percent"] == 17
assert status2["direct_prediction_pwm_percent"] == 42
assert fields2[14] == "17"
assert fields2[17] == "42"

print("AI Cooling v5.1 sparse-bucket direct diagnostics: PASS")
