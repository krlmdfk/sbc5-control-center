#!/usr/bin/env python3
from pathlib import Path
import json
import yaml

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected exactly one match in {path}: got {count} for {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# ---------------------------------------------------------------------------
# AI Cooling: bucket-aware qualified sampling v4.
# Preserve learned bins/EMA, but reset short qualification windows on bucket
# transitions so low-load history cannot poison medium/high qualification.
# ---------------------------------------------------------------------------
ai = APP / "ai_cooling.py"
replace_once(
    ai,
    'QUALIFICATION_POLICY = "quasi_steady_v3"\n',
    'QUALIFICATION_POLICY = "bucket_aware_quasi_steady_v4"\n',
)
replace_once(
    ai,
    "QUALIFY_STREAK_REQUIRED = 3\n",
    """QUALIFY_STREAK_REQUIRED = 3\n\n\ndef _qualification_limits(workload: str, deadband: float) -> dict[str, float | int]:\n    \"\"\"Return workload-aware quality gates without weakening steady-state learning.\n\n    Idle/low retain the proven strict v3 gates. Medium/high use a shorter clean\n    post-transition window and slightly wider thermal/PWM bounds because real\n    closed-loop equilibrium at higher load has more ripple. Transient ramps are\n    still rejected by slope/range checks.\n    \"\"\"\n    limits: dict[str, float | int] = {\n        \"temperature_band_c\": max(float(deadband), QUALIFY_TEMP_BAND_MIN_C),\n        \"slope_abs_max_c_per_min\": QUALIFY_SLOPE_MAX,\n        \"temperature_range_max_c\": QUALIFY_TEMP_RANGE_MAX_C,\n        \"temperature_window_min_span_seconds\": QUALIFY_TEMP_WINDOW_MIN_SPAN_SECONDS,\n        \"temperature_window_min_points\": QUALIFY_TEMP_WINDOW_MIN_POINTS,\n        \"pwm_range_max_percent\": QUALIFY_PWM_RANGE_MAX,\n        \"workload_stable_seconds\": WORKLOAD_STABLE_SECONDS,\n        \"stable_seconds_required\": QUALIFY_STABLE_SECONDS,\n    }\n    if workload == \"medium\":\n        limits.update({\n            \"temperature_band_c\": max(float(deadband), 2.0),\n            \"slope_abs_max_c_per_min\": 1.0,\n            \"temperature_range_max_c\": 3.0,\n            \"temperature_window_min_span_seconds\": 20.0,\n            \"temperature_window_min_points\": 3,\n            \"pwm_range_max_percent\": 12,\n            \"workload_stable_seconds\": 20.0,\n            \"stable_seconds_required\": 20.0,\n        })\n    elif workload == \"high\":\n        limits.update({\n            \"temperature_band_c\": max(float(deadband), 3.0),\n            \"slope_abs_max_c_per_min\": 1.5,\n            \"temperature_range_max_c\": 4.0,\n            \"temperature_window_min_span_seconds\": 20.0,\n            \"temperature_window_min_points\": 3,\n            \"pwm_range_max_percent\": 18,\n            \"workload_stable_seconds\": 20.0,\n            \"stable_seconds_required\": 20.0,\n        })\n    return limits\n""",
)
replace_once(
    ai,
    """    raw_load = _cpu_load(telemetry)\n    smoothed_load, workload, workload_age, workload_changed = _update_workload_state(model, raw_load, now)\n    pmic_power = telemetry.get(\"pmic_power_w\")\n    freq = telemetry.get(\"cpu_frequency_mhz\")\n\n    slope, temp_window_range, temp_window_span, temp_window_mean, temp_window_points = _update_temp_stability(model, temp, now)\n""",
    """    raw_load = _cpu_load(telemetry)\n    smoothed_load, workload, workload_age, workload_changed = _update_workload_state(model, raw_load, now)\n    pmic_power = telemetry.get(\"pmic_power_w\")\n    freq = telemetry.get(\"cpu_frequency_mhz\")\n\n    # A workload transition starts a fresh qualification window. Learned bins/EMA\n    # remain intact; only the short stability histories are cleared. Without this\n    # reset, a low->medium transition carries old low-load temperatures for up to\n    # 60 s and can make medium/high permanently fail temperature/range gates.\n    if workload_changed:\n        model[\"qualification_temp_history\"] = []\n        model[\"qualification_pwm_history\"] = []\n    qualification_limits = _qualification_limits(workload, deadband)\n    slope, temp_window_range, temp_window_span, temp_window_mean, temp_window_points = _update_temp_stability(model, temp, now)\n""",
)
replace_once(
    ai,
    """    qualification_band = max(deadband, QUALIFY_TEMP_BAND_MIN_C)\n    window_ready = temp_window_span >= QUALIFY_TEMP_WINDOW_MIN_SPAN_SECONDS and temp_window_points >= QUALIFY_TEMP_WINDOW_MIN_POINTS\n    window_error = temp_window_mean - target\n    # Current value may move by one sensor quantum while the minute-long operating\n    # point remains stable. The window mean is therefore authoritative for quality.\n    near_target = abs(window_error) <= qualification_band and abs(error) <= max(2.0, qualification_band * 1.6)\n    slope_stable = abs(slope) <= QUALIFY_SLOPE_MAX\n    temp_range_stable = temp_window_range <= QUALIFY_TEMP_RANGE_MAX_C\n    pwm_window_range, pwm_window_span = _update_pwm_stability(model, current, now)\n    pwm_stable = pwm_window_range <= QUALIFY_PWM_RANGE_MAX\n    workload_stable = workload_age >= WORKLOAD_STABLE_SECONDS\n""",
    """    qualification_band = float(qualification_limits[\"temperature_band_c\"])\n    window_ready = (\n        temp_window_span >= float(qualification_limits[\"temperature_window_min_span_seconds\"])\n        and temp_window_points >= int(qualification_limits[\"temperature_window_min_points\"])\n    )\n    window_error = temp_window_mean - target\n    # Current value may move by one sensor quantum while the operating point remains\n    # stable. The clean, bucket-local window mean is authoritative for quality.\n    near_target = abs(window_error) <= qualification_band and abs(error) <= max(2.0, qualification_band * 1.6)\n    slope_stable = abs(slope) <= float(qualification_limits[\"slope_abs_max_c_per_min\"])\n    temp_range_stable = temp_window_range <= float(qualification_limits[\"temperature_range_max_c\"])\n    pwm_window_range, pwm_window_span = _update_pwm_stability(model, current, now)\n    pwm_stable = pwm_window_range <= int(qualification_limits[\"pwm_range_max_percent\"])\n    workload_stable = workload_age >= float(qualification_limits[\"workload_stable_seconds\"])\n""",
)
replace_once(
    ai,
    """    qualified = observation_added and stable_candidate and stable_seconds >= QUALIFY_STABLE_SECONDS\n""",
    """    qualified = observation_added and stable_candidate and stable_seconds >= float(qualification_limits[\"stable_seconds_required\"])\n""",
)
replace_once(
    ai,
    """        quality_weight = 1.0 if qualification_tier == \"gold\" else 0.55\n""",
    """        quality_weight = 1.0 if qualification_tier == \"gold\" else (0.55 if workload in {\"idle\", \"low\"} else (0.45 if workload == \"medium\" else 0.40))\n""",
)
replace_once(
    ai,
    """        \"stable_seconds_required\": int(QUALIFY_STABLE_SECONDS),\n""",
    """        \"stable_seconds_required\": int(qualification_limits[\"stable_seconds_required\"]),\n""",
)
replace_once(
    ai,
    """        \"qualification_limits\": {\n            \"temperature_band_c\": qualification_band,\n            \"slope_abs_max_c_per_min\": QUALIFY_SLOPE_MAX,\n            \"temperature_range_max_c\": QUALIFY_TEMP_RANGE_MAX_C,\n            \"temperature_window_seconds\": QUALIFY_TEMP_WINDOW_SECONDS,\n            \"temperature_window_min_span_seconds\": QUALIFY_TEMP_WINDOW_MIN_SPAN_SECONDS,\n            \"temperature_window_min_points\": QUALIFY_TEMP_WINDOW_MIN_POINTS,\n            \"pwm_range_max_percent\": QUALIFY_PWM_RANGE_MAX,\n            \"pwm_window_seconds\": QUALIFY_PWM_WINDOW_SECONDS,\n            \"workload_window_seconds\": WORKLOAD_WINDOW_SECONDS,\n            \"workload_stable_seconds\": WORKLOAD_STABLE_SECONDS,\n            \"workload_hysteresis_percent\": WORKLOAD_HYSTERESIS_PERCENT,\n        },\n""",
    """        \"qualification_limits\": {\n            \"temperature_band_c\": qualification_band,\n            \"slope_abs_max_c_per_min\": float(qualification_limits[\"slope_abs_max_c_per_min\"]),\n            \"temperature_range_max_c\": float(qualification_limits[\"temperature_range_max_c\"]),\n            \"temperature_window_seconds\": QUALIFY_TEMP_WINDOW_SECONDS,\n            \"temperature_window_min_span_seconds\": float(qualification_limits[\"temperature_window_min_span_seconds\"]),\n            \"temperature_window_min_points\": int(qualification_limits[\"temperature_window_min_points\"]),\n            \"pwm_range_max_percent\": int(qualification_limits[\"pwm_range_max_percent\"]),\n            \"pwm_window_seconds\": QUALIFY_PWM_WINDOW_SECONDS,\n            \"workload_window_seconds\": WORKLOAD_WINDOW_SECONDS,\n            \"workload_stable_seconds\": float(qualification_limits[\"workload_stable_seconds\"]),\n            \"workload_hysteresis_percent\": WORKLOAD_HYSTERESIS_PERCENT,\n            \"bucket_aware\": True,\n        },\n""",
)

# ---------------------------------------------------------------------------
# Adaptive PWM: upward-only thermal fast path. Existing safety_max and 70C kernel
# handoff remain untouched; downward slew remains conservative.
# ---------------------------------------------------------------------------
run = APP / "run_legacy.sh"
replace_once(
    run,
    "local adaptive_trim_limit=12 slew_up_step=3 slew_down_step=4 slew_fast_up_step=5 slew_fast_down_step=5 trim_decay_interval_cycles=1",
    "local adaptive_trim_limit=12 slew_up_step=3 slew_down_step=4 slew_fast_down_step=5 thermal_fast_delta=5000 thermal_critical_delta=7000 thermal_fast_up_step=8 thermal_critical_up_step=12 trim_decay_interval_cycles=1",
)
replace_once(
    run,
    """      step_up=\"$slew_up_step\"; step_down=\"$slew_down_step\"\n      [ \"$error\" -ge \"$fast_delta\" ] 2>/dev/null && step_up=\"$slew_fast_up_step\"\n      [ \"$error\" -le $((-down_fast_delta)) ] 2>/dev/null && step_down=\"$slew_fast_down_step\"\n""",
    """      step_up=\"$slew_up_step\"; step_down=\"$slew_down_step\"\n      if [ \"$error\" -ge \"$thermal_critical_delta\" ] 2>/dev/null; then\n        step_up=\"$thermal_critical_up_step\"; action=\"${action}_thermal_critical\"\n      elif [ \"$error\" -ge \"$thermal_fast_delta\" ] 2>/dev/null; then\n        step_up=\"$thermal_fast_up_step\"; action=\"${action}_thermal_fast\"\n      fi\n      [ \"$error\" -le $((-down_fast_delta)) ] 2>/dev/null && step_down=\"$slew_fast_down_step\"\n""",
)
text = run.read_text(encoding="utf-8")
text = text.replace(
    "actuator slew=+3/-4pp na cykl (fast +5/-5)",
    "actuator slew=+3/-4pp na cykl (thermal +8@+5C/+12@+7C; fast down -5)",
)
run.write_text(text, encoding="utf-8")

# ---------------------------------------------------------------------------
# Restart provenance UX: distinguish the current release from a previously
# pending boot/config request using existing Restart Manager attributes.
# ---------------------------------------------------------------------------
card = ROOT / "dashboard" / "update_status_card.yaml"
replace_once(
    card,
    "            secondary: Dokończ aktualizację po bezpiecznym sprawdzeniu konfiguracji\n",
    """            secondary: >-\n              {% set reason = state_attr('sensor.sbc5_fan_restart_required','reason') | default('', true) %}\n              {% set post = state_attr('sensor.sbc5_fan_restart_required','post_update') | default(false, true) %}\n              {% if post %}\n                Źródło: aktualizacja · {{ reason | default('wymagane przeładowanie Home Assistant', true) }}\n              {% else %}\n                Źródło: wcześniejsze żądanie · niezależne od bieżącego wydania · {{ reason | default('Restart Manager', true) }}\n              {% endif %}\n""",
)
replace_once(
    card,
    "            secondary: Zmiany boot/config.txt zaczną działać po restarcie hosta\n",
    """            secondary: >-\n              {% set reason = state_attr('sensor.sbc5_fan_restart_required','reason') | default('', true) %}\n              {% set r = reason | lower %}\n              {% set post = state_attr('sensor.sbc5_fan_restart_required','post_update') | default(false, true) %}\n              {% if 'cpu' in r or 'overclock' in r or 'arm_freq' in r %}\n                Źródło: profil CPU/OC · {{ reason }}\n              {% elif 'gpu' in r or 'v3d' in r or 'isp' in r %}\n                Źródło: profil GPU/V3D/ISP · {{ reason }}\n              {% elif 'fan' in r or 'cool' in r or 'overlay' in r or 'custom1' in r %}\n                Źródło: profil chłodzenia/Device Tree · {{ reason }}\n              {% elif 'config' in r or 'boot' in r or 'usb' in r %}\n                Źródło: konfiguracja boot/config.txt · {{ reason }}\n              {% elif post %}\n                Źródło: aktualizacja · {{ reason | default('restart zadeklarowany przez wydanie', true) }}\n              {% else %}\n                Źródło: wcześniejsza konfiguracja · niezależne od bieżącego wydania · {{ reason | default('Restart Manager', true) }}\n              {% endif %}\n""",
)
# Keep the shipped JSON card synchronized with the canonical YAML card.
parsed = yaml.safe_load(card.read_text(encoding="utf-8"))
(APP / "update_status_card.json").write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ---------------------------------------------------------------------------
# Current-state docs only (history remains in CHANGELOG/release notes).
# ---------------------------------------------------------------------------
info = ROOT / "INFO.md"
text = info.read_text(encoding="utf-8")
text = text.replace(
    "AI Cooling runs locally and is secondary to the classical controller. The model distinguishes `idle`, `low`, `medium` and `high` workload buckets, qualifies samples and can operate in a limited Assist mode.",
    "AI Cooling runs locally and is secondary to the classical controller. The model distinguishes `idle`, `low`, `medium` and `high` workload buckets. Qualified learning uses bucket-local stability windows: `idle/low` keep strict steady-state gates, while `medium/high` use workload-aware thermal/PWM limits so stable higher-load operation can mature without learning transient temperature ramps. Assist remains bounded and the learned model is persistent.",
)
text = text.replace(
    "AI Cooling działa lokalnie i wtórnie wobec klasycznego regulatora. Model rozróżnia buckety `idle`, `low`, `medium` i `high`, kwalifikuje próbki jakościowe oraz może pracować w ograniczonym trybie Assist.",
    "AI Cooling działa lokalnie i wtórnie wobec klasycznego regulatora. Model rozróżnia buckety `idle`, `low`, `medium` i `high`. Uczenie jakościowe korzysta z osobnych okien stabilności dla bieżącego bucketa: `idle/low` zachowują ścisłe kryteria stanu ustalonego, a `medium/high` używają limitów temperatury/PWM dopasowanych do obciążenia, dzięki czemu stabilna praca pod większym obciążeniem może dojrzewać bez uczenia skoków przejściowych. Assist pozostaje ograniczony, a wyuczony model jest trwały.",
)
info.write_text(text, encoding="utf-8")

for doc in (ROOT / "DOCUMENTATION.md", ROOT / "docs" / "ai-cooling.md"):
    text = doc.read_text(encoding="utf-8")
    marker = "## Bucket-aware qualified learning / Uczenie jakościowe zależne od bucketa"
    if marker not in text:
        text += """\n\n## Bucket-aware qualified learning / Uczenie jakościowe zależne od bucketa\n\n**EN.** AI Cooling keeps separate workload buckets (`idle`, `low`, `medium`, `high`). A bucket transition starts a fresh short-term qualification window, while learned PWM estimates, counters and confidence history remain persistent. `idle/low` use the strict steady-state gates. `medium/high` permit wider thermal/PWM ripple but still reject fast temperature ramps, wide ranges and unstable workload. This prevents low-load samples from contaminating higher-load qualification without teaching the model transient spikes.\n\nAdaptive PWM remains curve-anchored. Normal upward slew is +3 pp per controller cycle; when CPU temperature is at least 5°C above target, the upward thermal fast path permits up to +8 pp/cycle, and at least 7°C above target up to +12 pp/cycle. Emergency 100% cooling and kernel handoff remain authoritative. Downward slew remains conservative.\n\n**PL.** AI Cooling utrzymuje osobne buckety obciążenia (`idle`, `low`, `medium`, `high`). Zmiana bucketa rozpoczyna świeże krótkie okno kwalifikacji, ale wyuczone estymaty PWM, liczniki i historia confidence pozostają trwałe. `idle/low` korzystają ze ścisłych kryteriów stanu ustalonego. `medium/high` dopuszczają większe tętnienia temperatury/PWM, lecz nadal odrzucają szybkie trendy temperatury, zbyt szeroki zakres i niestabilne obciążenie. Dzięki temu próbki z niskiego obciążenia nie zanieczyszczają kwalifikacji wyższych bucketów, a model nie uczy się skoków przejściowych.\n\nAdaptive PWM pozostaje zakotwiczony w krzywej. Normalny wzrost ma limit +3 pp na cykl regulatora; od 5°C powyżej celu thermal fast path pozwala na maks. +8 pp/cykl, a od 7°C powyżej celu na maks. +12 pp/cykl. Awaryjne 100% i przekazanie sterowania do kernela pozostają nadrzędne. Zmniejszanie PWM pozostaje zachowawcze.\n"""
        doc.write_text(text, encoding="utf-8")

# ---------------------------------------------------------------------------
# Regression tests and CI hook.
# ---------------------------------------------------------------------------
test = ROOT / "scripts" / "test_ai_bucket_qualification_v4.py"
test.write_text(r'''#!/usr/bin/env python3
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI_PATH = ROOT / "local_apps" / "sbc5_control_center" / "ai_cooling.py"
RUN_PATH = ROOT / "local_apps" / "sbc5_control_center" / "run_legacy.sh"
CARD_PATH = ROOT / "dashboard" / "update_status_card.yaml"

spec = spec_from_file_location("sbc5_ai_cooling", AI_PATH)
assert spec and spec.loader
ai = module_from_spec(spec)
spec.loader.exec_module(ai)

assert ai.QUALIFICATION_POLICY == "bucket_aware_quasi_steady_v4"
low = ai._qualification_limits("low", 0.75)
medium = ai._qualification_limits("medium", 0.75)
high = ai._qualification_limits("high", 0.75)
assert low["temperature_band_c"] == 1.25
assert medium["temperature_band_c"] == 2.0
assert high["temperature_band_c"] == 3.0
assert medium["temperature_window_min_span_seconds"] == 20.0
assert high["pwm_range_max_percent"] == 18
assert low["slope_abs_max_c_per_min"] < medium["slope_abs_max_c_per_min"] < high["slope_abs_max_c_per_min"]

model = {
    "schema": ai.SCHEMA,
    "qualification_policy": "quasi_steady_v3",
    "bins": {"49.0|low": {"qualified_n": 171, "ema_pwm": 44.0, "observations": 14477}},
    "qualification_temp_history": [{"epoch": 1, "temp_c": 49.0}],
    "qualification_pwm_history": [{"epoch": 1, "pwm": 44}],
}
migrated = ai._migrate_model(model, 1000.0)
assert migrated["bins"]["49.0|low"]["qualified_n"] == 171
assert migrated["bins"]["49.0|low"]["ema_pwm"] == 44.0
assert migrated.get("qualification_temp_history") == []
assert migrated.get("qualification_pwm_history") == []

source = AI_PATH.read_text(encoding="utf-8")
assert 'if workload_changed:' in source
assert 'model["qualification_temp_history"] = []' in source
assert 'model["qualification_pwm_history"] = []' in source

run = RUN_PATH.read_text(encoding="utf-8")
assert "thermal_fast_delta=5000" in run
assert "thermal_critical_delta=7000" in run
assert "thermal_fast_up_step=8" in run
assert "thermal_critical_up_step=12" in run
assert run.index('error" -ge "$thermal_critical_delta') < run.index('error" -ge "$thermal_fast_delta')
assert "emergency_temperature_handoff" in run

card = CARD_PATH.read_text(encoding="utf-8")
assert "Źródło: profil CPU/OC" in card
assert "Źródło: profil GPU/V3D/ISP" in card
assert "niezależne od bieżącego wydania" in card
print("AI bucket qualification v4 / thermal fast path / restart provenance: PASS")
''', encoding="utf-8")

validate = ROOT / ".github" / "workflows" / "validate.yml"
replace_once(
    validate,
    """      - name: Test Thermal Predictor Accuracy Calibration\n        run: python scripts/test_thermal_predictor_accuracy.py\n\n""",
    """      - name: Test Thermal Predictor Accuracy Calibration\n        run: python scripts/test_thermal_predictor_accuracy.py\n\n      - name: Test AI bucket-aware qualification and thermal fast path\n        run: python scripts/test_ai_bucket_qualification_v4.py\n\n""",
)

print("Prepared source changes for SBC5 3.1.7")
