#!/usr/bin/env python3
"""Regression tests for the read-only SBC5 thermal log analyzer."""
from pathlib import Path
import importlib.util
import tempfile

root = Path(__file__).resolve().parents[1]
path = root / "scripts/analyze_thermal_control_logs.py"
spec = importlib.util.spec_from_file_location("thermal_log_audit_test", path)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

logs = [
    "[2026-11-10 18:02:40] Thermal Predictor: mode=guided_assist; F30=50.05C F60=49.22C F120=49.08C; confidence=77%; MAE_avg=1.458C; weighted=48.72C error=-0.28C; TP_applied=0pp; gate=probation/quality_probation; decision=near_target.",
    "[2026-11-10 18:03:22] Adaptive PWM: T_raw=49.1°C T_control=49.5°C target=49.0°C trend30=-0.75C/min curve=46% applied=49% owner=adaptive.",
    "[2026-11-10 18:03:43] Thermal Predictor: mode=guided_assist; F30=51.35C F60=51.68C F120=50.93C; confidence=80%; MAE_avg=1.249C; weighted=50.11C error=1.11C; TP_applied=0pp; gate=active/eligible.",
    "[2026-11-10 18:04:25] Adaptive PWM: T_raw=50.2°C T_control=50.5°C target=49.0°C trend30=1.54C/min applied=54% owner=adaptive.",
    "[2026-11-10 18:04:45] Thermal Predictor: F30=49.99C F60=50.02C F120=50.56C; confidence=77%; MAE_avg=1.411C; TP_applied=1pp; gate=probation/quality_probation.",
    "[2026-11-10 18:05:00] AI Cooling: state=assist; bucket=low; observations_total=51590; qualified_samples_total=1580; qualification=temperature.",
    "[2026-11-10 18:05:30] AI Cooling: state=assist; bucket=low; observations_total=51591; qualified_samples_total=1580; qualification=temperature_trend.",
]
result=module.analyze(logs)
assert result["thermal_samples"] == 3, result
assert result["actuator_samples"] == 2, result
assert result["ai_samples"] == 2, result
assert result["thermal"]["gate_snapshots"] == {"probation": 2, "active": 1}, result
assert result["thermal"]["gate_changes_between_snapshots"] == 2, result
assert result["thermal"]["f30_largest_logged_jump_c"] == 1.36, result
assert result["actuator"]["sample_mean_abs_temp_error_c"] == 0.65, result
assert result["actuator"]["pwm_min_percent"] == 49, result
assert result["actuator"]["pwm_max_percent"] == 54, result
assert result["ai"]["observations_delta"] == 1, result
assert result["ai"]["qualified_delta"] == 0, result
assert any("cannot reconstruct" in v for v in result["limitations"]), result
assert "forecast_mae" not in result, result

with tempfile.TemporaryDirectory() as scratch:
    sample_path = Path(scratch)/"example.log"
    sample_path.write_text("\n".join(logs) + "\n", encoding="utf-8")
    before = sample_path.read_bytes()
    with sample_path.open("r", encoding="utf-8") as f:
        module.analyze(f)
    assert sample_path.read_bytes() == before, "Read-only analysis must preserve source logs"

empty = module.analyze(["invalid", "some other line"])
assert empty["thermal_samples"] == 0
assert empty["actuator_samples"] == 0
assert empty["ai_samples"] == 0
print("Thermal log analysis read-only regression: PASS")
