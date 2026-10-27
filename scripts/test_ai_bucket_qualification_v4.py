#!/usr/bin/env python3
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
AI=ROOT/"local_apps"/"sbc5_control_center"/"ai_cooling.py"
RUN=ROOT/"local_apps"/"sbc5_control_center"/"run_legacy.sh"
CARD=ROOT/"dashboard"/"update_status_card.yaml"
spec=spec_from_file_location("sbc5_ai",AI); assert spec and spec.loader
ai=module_from_spec(spec); spec.loader.exec_module(ai)
assert ai.QUALIFICATION_POLICY=="bucket_aware_quasi_steady_v4"
low=ai._qualification_limits("low",0.75); med=ai._qualification_limits("medium",0.75); high=ai._qualification_limits("high",0.75)
assert low["temperature_band_c"]==1.25
assert med["temperature_band_c"]==2.0 and high["temperature_band_c"]==3.0
assert med["temperature_window_min_span_seconds"]==20.0 and high["pwm_range_max_percent"]==18
assert low["slope_abs_max_c_per_min"] < med["slope_abs_max_c_per_min"] < high["slope_abs_max_c_per_min"]
model={"schema":ai.SCHEMA,"qualification_policy":"quasi_steady_v3","bins":{"49.0|low":{"qualified_n":171,"ema_pwm":44.0,"observations":14477}},"qualification_temp_history":[{"epoch":1,"temp_c":49.0}],"qualification_pwm_history":[{"epoch":1,"pwm":44}]}
m=ai._migrate_model(model,1000.0)
assert m["bins"]["49.0|low"]["qualified_n"]==171 and m["bins"]["49.0|low"]["ema_pwm"]==44.0
assert m.get("qualification_temp_history")==[] and m.get("qualification_pwm_history")==[]
s=AI.read_text(encoding="utf-8"); assert "if workload_changed:" in s and "qualification_pwm_history" in s
r=RUN.read_text(encoding="utf-8"); assert "thermal_fast_delta=5000" in r and "thermal_critical_delta=7000" in r and "thermal_fast_up_step=8" in r and "thermal_critical_up_step=12" in r and "emergency_temperature_handoff" in r
c=CARD.read_text(encoding="utf-8"); assert "Źródło: profil CPU/OC" in c and "niezależne od bieżącego wydania" in c
print("AI bucket qualification v4 / thermal fast path / restart provenance: PASS")
