#!/usr/bin/env python3
from pathlib import Path
import json
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"


def sub_once(path: Path, pattern: str, replacement: str, *, flags: int = 0) -> None:
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        raise SystemExit(f"Expected one match in {path}: {pattern[:100]!r}; got {count}")
    path.write_text(updated, encoding="utf-8")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"Expected one literal match in {path}: {old[:100]!r}; got {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# AI Cooling — bucket-aware qualified sampling v4.
ai = APP / "ai_cooling.py"
sub_once(ai, r'QUALIFICATION_POLICY = "quasi_steady_v3"', 'QUALIFICATION_POLICY = "bucket_aware_quasi_steady_v4"')
sub_once(
    ai,
    r'(?m)^QUALIFY_STREAK_REQUIRED = 3.*$',
    '''QUALIFY_STREAK_REQUIRED = 3    # compatibility/diagnostic counter; time gate is authoritative


def _qualification_limits(workload: str, deadband: float) -> dict[str, float | int]:
    """Return workload-aware quality gates while preserving strict low-load learning."""
    limits: dict[str, float | int] = {
        "temperature_band_c": max(float(deadband), QUALIFY_TEMP_BAND_MIN_C),
        "slope_abs_max_c_per_min": QUALIFY_SLOPE_MAX,
        "temperature_range_max_c": QUALIFY_TEMP_RANGE_MAX_C,
        "temperature_window_min_span_seconds": QUALIFY_TEMP_WINDOW_MIN_SPAN_SECONDS,
        "temperature_window_min_points": QUALIFY_TEMP_WINDOW_MIN_POINTS,
        "pwm_range_max_percent": QUALIFY_PWM_RANGE_MAX,
        "workload_stable_seconds": WORKLOAD_STABLE_SECONDS,
        "stable_seconds_required": QUALIFY_STABLE_SECONDS,
    }
    if workload == "medium":
        limits.update({
            "temperature_band_c": max(float(deadband), 2.0),
            "slope_abs_max_c_per_min": 1.0,
            "temperature_range_max_c": 3.0,
            "temperature_window_min_span_seconds": 20.0,
            "temperature_window_min_points": 3,
            "pwm_range_max_percent": 12,
            "workload_stable_seconds": 20.0,
            "stable_seconds_required": 20.0,
        })
    elif workload == "high":
        limits.update({
            "temperature_band_c": max(float(deadband), 3.0),
            "slope_abs_max_c_per_min": 1.5,
            "temperature_range_max_c": 4.0,
            "temperature_window_min_span_seconds": 20.0,
            "temperature_window_min_points": 3,
            "pwm_range_max_percent": 18,
            "workload_stable_seconds": 20.0,
            "stable_seconds_required": 20.0,
        })
    return limits''',
)
replace_once(
    ai,
    '''    raw_load = _cpu_load(telemetry)
    smoothed_load, workload, workload_age, workload_changed = _update_workload_state(model, raw_load, now)
    pmic_power = telemetry.get("pmic_power_w")
    freq = telemetry.get("cpu_frequency_mhz")

    slope, temp_window_range, temp_window_span, temp_window_mean, temp_window_points = _update_temp_stability(model, temp, now)
''',
    '''    raw_load = _cpu_load(telemetry)
    smoothed_load, workload, workload_age, workload_changed = _update_workload_state(model, raw_load, now)
    pmic_power = telemetry.get("pmic_power_w")
    freq = telemetry.get("cpu_frequency_mhz")

    # A bucket transition gets a clean short-term quality window. Learned bins,
    # EMA values, observations and qualified counters are deliberately preserved.
    if workload_changed:
        model["qualification_temp_history"] = []
        model["qualification_pwm_history"] = []
    qualification_limits = _qualification_limits(workload, deadband)
    slope, temp_window_range, temp_window_span, temp_window_mean, temp_window_points = _update_temp_stability(model, temp, now)
''',
)
replace_once(
    ai,
    '''    qualification_band = max(deadband, QUALIFY_TEMP_BAND_MIN_C)
    window_ready = temp_window_span >= QUALIFY_TEMP_WINDOW_MIN_SPAN_SECONDS and temp_window_points >= QUALIFY_TEMP_WINDOW_MIN_POINTS
    window_error = temp_window_mean - target
    # Current value may move by one sensor quantum while the minute-long operating
    # point remains stable. The window mean is therefore authoritative for quality.
    near_target = abs(window_error) <= qualification_band and abs(error) <= max(2.0, qualification_band * 1.6)
    slope_stable = abs(slope) <= QUALIFY_SLOPE_MAX
    temp_range_stable = temp_window_range <= QUALIFY_TEMP_RANGE_MAX_C
    pwm_window_range, pwm_window_span = _update_pwm_stability(model, current, now)
    pwm_stable = pwm_window_range <= QUALIFY_PWM_RANGE_MAX
    workload_stable = workload_age >= WORKLOAD_STABLE_SECONDS
''',
    '''    qualification_band = float(qualification_limits["temperature_band_c"])
    window_ready = (
        temp_window_span >= float(qualification_limits["temperature_window_min_span_seconds"])
        and temp_window_points >= int(qualification_limits["temperature_window_min_points"])
    )
    window_error = temp_window_mean - target
    # The clean bucket-local window mean is authoritative for quality.
    near_target = abs(window_error) <= qualification_band and abs(error) <= max(2.0, qualification_band * 1.6)
    slope_stable = abs(slope) <= float(qualification_limits["slope_abs_max_c_per_min"])
    temp_range_stable = temp_window_range <= float(qualification_limits["temperature_range_max_c"])
    pwm_window_range, pwm_window_span = _update_pwm_stability(model, current, now)
    pwm_stable = pwm_window_range <= int(qualification_limits["pwm_range_max_percent"])
    workload_stable = workload_age >= float(qualification_limits["workload_stable_seconds"])
''',
)
replace_once(ai, '    qualified = observation_added and stable_candidate and stable_seconds >= QUALIFY_STABLE_SECONDS\n', '    qualified = observation_added and stable_candidate and stable_seconds >= float(qualification_limits["stable_seconds_required"])\n')
replace_once(ai, '        quality_weight = 1.0 if qualification_tier == "gold" else 0.55\n', '        quality_weight = 1.0 if qualification_tier == "gold" else (0.55 if workload in {"idle", "low"} else (0.45 if workload == "medium" else 0.40))\n')
replace_once(ai, '        "stable_seconds_required": int(QUALIFY_STABLE_SECONDS),\n', '        "stable_seconds_required": int(qualification_limits["stable_seconds_required"]),\n')
replace_once(
    ai,
    '''        "qualification_limits": {
            "temperature_band_c": qualification_band,
            "slope_abs_max_c_per_min": QUALIFY_SLOPE_MAX,
            "temperature_range_max_c": QUALIFY_TEMP_RANGE_MAX_C,
            "temperature_window_seconds": QUALIFY_TEMP_WINDOW_SECONDS,
            "temperature_window_min_span_seconds": QUALIFY_TEMP_WINDOW_MIN_SPAN_SECONDS,
            "temperature_window_min_points": QUALIFY_TEMP_WINDOW_MIN_POINTS,
            "pwm_range_max_percent": QUALIFY_PWM_RANGE_MAX,
            "pwm_window_seconds": QUALIFY_PWM_WINDOW_SECONDS,
            "workload_window_seconds": WORKLOAD_WINDOW_SECONDS,
            "workload_stable_seconds": WORKLOAD_STABLE_SECONDS,
            "workload_hysteresis_percent": WORKLOAD_HYSTERESIS_PERCENT,
        },
''',
    '''        "qualification_limits": {
            "temperature_band_c": qualification_band,
            "slope_abs_max_c_per_min": float(qualification_limits["slope_abs_max_c_per_min"]),
            "temperature_range_max_c": float(qualification_limits["temperature_range_max_c"]),
            "temperature_window_seconds": QUALIFY_TEMP_WINDOW_SECONDS,
            "temperature_window_min_span_seconds": float(qualification_limits["temperature_window_min_span_seconds"]),
            "temperature_window_min_points": int(qualification_limits["temperature_window_min_points"]),
            "pwm_range_max_percent": int(qualification_limits["pwm_range_max_percent"]),
            "pwm_window_seconds": QUALIFY_PWM_WINDOW_SECONDS,
            "workload_window_seconds": WORKLOAD_WINDOW_SECONDS,
            "workload_stable_seconds": float(qualification_limits["workload_stable_seconds"]),
            "workload_hysteresis_percent": WORKLOAD_HYSTERESIS_PERCENT,
            "bucket_aware": True,
        },
''',
)

# Adaptive PWM — upward-only thermal fast path. Emergency handoff unchanged.
run = APP / "run_legacy.sh"
replace_once(
    run,
    'local adaptive_trim_limit=12 slew_up_step=3 slew_down_step=4 slew_fast_up_step=5 slew_fast_down_step=5 trim_decay_interval_cycles=1',
    'local adaptive_trim_limit=12 slew_up_step=3 slew_down_step=4 slew_fast_down_step=5 thermal_fast_delta=5000 thermal_critical_delta=7000 thermal_fast_up_step=8 thermal_critical_up_step=12 trim_decay_interval_cycles=1',
)
replace_once(
    run,
    '''      step_up="$slew_up_step"; step_down="$slew_down_step"
      [ "$error" -ge "$fast_delta" ] 2>/dev/null && step_up="$slew_fast_up_step"
      [ "$error" -le $((-down_fast_delta)) ] 2>/dev/null && step_down="$slew_fast_down_step"
''',
    '''      step_up="$slew_up_step"; step_down="$slew_down_step"
      if [ "$error" -ge "$thermal_critical_delta" ] 2>/dev/null; then
        step_up="$thermal_critical_up_step"; action="${action}_thermal_critical"
      elif [ "$error" -ge "$thermal_fast_delta" ] 2>/dev/null; then
        step_up="$thermal_fast_up_step"; action="${action}_thermal_fast"
      fi
      [ "$error" -le $((-down_fast_delta)) ] 2>/dev/null && step_down="$slew_fast_down_step"
''',
)

# Restart provenance in the update card.
card = ROOT / "dashboard" / "update_status_card.yaml"
replace_once(
    card,
    '            secondary: Dokończ aktualizację po bezpiecznym sprawdzeniu konfiguracji\n',
    '''            secondary: >-
              {% set reason = state_attr('sensor.sbc5_fan_restart_required','reason') | default('', true) %}
              {% set post = state_attr('sensor.sbc5_fan_restart_required','post_update') | default(false, true) %}
              {% if post %}
                Źródło: aktualizacja · {{ reason | default('wymagane przeładowanie Home Assistant', true) }}
              {% else %}
                Źródło: wcześniejsze żądanie · niezależne od bieżącego wydania · {{ reason | default('Restart Manager', true) }}
              {% endif %}
''',
)
replace_once(
    card,
    '            secondary: Zmiany boot/config.txt zaczną działać po restarcie hosta\n',
    '''            secondary: >-
              {% set reason = state_attr('sensor.sbc5_fan_restart_required','reason') | default('', true) %}
              {% set r = reason | lower %}
              {% set post = state_attr('sensor.sbc5_fan_restart_required','post_update') | default(false, true) %}
              {% if 'cpu' in r or 'overclock' in r or 'arm_freq' in r %}
                Źródło: profil CPU/OC · {{ reason }}
              {% elif 'gpu' in r or 'v3d' in r or 'isp' in r %}
                Źródło: profil GPU/V3D/ISP · {{ reason }}
              {% elif 'fan' in r or 'cool' in r or 'overlay' in r or 'custom1' in r %}
                Źródło: profil chłodzenia/Device Tree · {{ reason }}
              {% elif 'config' in r or 'boot' in r or 'usb' in r %}
                Źródło: konfiguracja boot/config.txt · {{ reason }}
              {% elif post %}
                Źródło: aktualizacja · {{ reason | default('restart zadeklarowany przez wydanie', true) }}
              {% else %}
                Źródło: wcześniejsza konfiguracja · niezależne od bieżącego wydania · {{ reason | default('Restart Manager', true) }}
              {% endif %}
''',
)
parsed = yaml.safe_load(card.read_text(encoding="utf-8"))
(APP / "update_status_card.json").write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Current-state docs only; history is generated by release_prepare.py.
info = ROOT / "INFO.md"
text = info.read_text(encoding="utf-8")
text = text.replace(
    "AI Cooling runs locally and is secondary to the classical controller. The model distinguishes `idle`, `low`, `medium` and `high` workload buckets, qualifies samples and can operate in a limited Assist mode.",
    "AI Cooling runs locally and is secondary to the classical controller. The model distinguishes `idle`, `low`, `medium` and `high` workload buckets. Qualified learning uses bucket-local stability windows: `idle/low` keep strict steady-state gates, while `medium/high` use workload-aware thermal/PWM limits. Assist remains bounded and the learned model is persistent.",
)
text = text.replace(
    "AI Cooling działa lokalnie i wtórnie wobec klasycznego regulatora. Model rozróżnia buckety `idle`, `low`, `medium` i `high`, kwalifikuje próbki jakościowe oraz może pracować w ograniczonym trybie Assist.",
    "AI Cooling działa lokalnie i wtórnie wobec klasycznego regulatora. Model rozróżnia buckety `idle`, `low`, `medium` i `high`. Uczenie jakościowe korzysta z okien stabilności bieżącego bucketa: `idle/low` zachowują ścisłe kryteria, a `medium/high` używają limitów temperatury/PWM dopasowanych do obciążenia. Assist pozostaje ograniczony, a wyuczony model jest trwały.",
)
info.write_text(text, encoding="utf-8")

section = '''\n\n## Bucket-aware qualified learning / Uczenie jakościowe zależne od bucketa\n\n**EN.** A workload-bucket transition starts a fresh short-term qualification window while learned PWM estimates, counters and confidence history remain persistent. `idle/low` retain strict steady-state gates. `medium/high` permit wider thermal/PWM ripple but still reject fast temperature ramps, wide ranges and unstable workload. Adaptive PWM remains curve-anchored; normal upward slew is +3 pp/cycle, target+5°C permits up to +8 pp/cycle, and target+7°C permits up to +12 pp/cycle. Emergency 100% cooling and kernel handoff remain authoritative; downward slew remains conservative.\n\n**PL.** Zmiana bucketa rozpoczyna świeże krótkie okno kwalifikacji, ale wyuczone estymaty PWM, liczniki i historia confidence pozostają trwałe. `idle/low` zachowują ścisłe kryteria stanu ustalonego. `medium/high` dopuszczają większe tętnienia temperatury/PWM, lecz nadal odrzucają szybkie trendy temperatury, zbyt szeroki zakres i niestabilne obciążenie. Adaptive PWM pozostaje zakotwiczony w krzywej; normalny wzrost to +3 pp/cykl, od target+5°C maks. +8 pp/cykl, a od target+7°C maks. +12 pp/cykl. Awaryjne 100% i przekazanie sterowania kernelowi pozostają nadrzędne; zmniejszanie PWM pozostaje zachowawcze.\n'''
for doc in (ROOT / "DOCUMENTATION.md", ROOT / "docs" / "ai-cooling.md"):
    text = doc.read_text(encoding="utf-8")
    if "## Bucket-aware qualified learning / Uczenie jakościowe zależne od bucketa" not in text:
        doc.write_text(text + section, encoding="utf-8")

# Regression test.
test = ROOT / "scripts" / "test_ai_bucket_qualification_v4.py"
test.write_text('''#!/usr/bin/env python3\nfrom importlib.util import module_from_spec, spec_from_file_location\nfrom pathlib import Path\nROOT=Path(__file__).resolve().parents[1]\nAI=ROOT/"local_apps"/"sbc5_control_center"/"ai_cooling.py"\nRUN=ROOT/"local_apps"/"sbc5_control_center"/"run_legacy.sh"\nCARD=ROOT/"dashboard"/"update_status_card.yaml"\nspec=spec_from_file_location("sbc5_ai",AI); assert spec and spec.loader\nai=module_from_spec(spec); spec.loader.exec_module(ai)\nassert ai.QUALIFICATION_POLICY=="bucket_aware_quasi_steady_v4"\nlow=ai._qualification_limits("low",0.75); med=ai._qualification_limits("medium",0.75); high=ai._qualification_limits("high",0.75)\nassert low["temperature_band_c"]==1.25\nassert med["temperature_band_c"]==2.0 and high["temperature_band_c"]==3.0\nassert med["temperature_window_min_span_seconds"]==20.0 and high["pwm_range_max_percent"]==18\nassert low["slope_abs_max_c_per_min"] < med["slope_abs_max_c_per_min"] < high["slope_abs_max_c_per_min"]\nmodel={"schema":ai.SCHEMA,"qualification_policy":"quasi_steady_v3","bins":{"49.0|low":{"qualified_n":171,"ema_pwm":44.0,"observations":14477}},"qualification_temp_history":[{"epoch":1,"temp_c":49.0}],"qualification_pwm_history":[{"epoch":1,"pwm":44}]}\nm=ai._migrate_model(model,1000.0)\nassert m["bins"]["49.0|low"]["qualified_n"]==171 and m["bins"]["49.0|low"]["ema_pwm"]==44.0\nassert m.get("qualification_temp_history")==[] and m.get("qualification_pwm_history")==[]\ns=AI.read_text(encoding="utf-8"); assert "if workload_changed:" in s and "qualification_pwm_history" in s\nr=RUN.read_text(encoding="utf-8"); assert "thermal_fast_delta=5000" in r and "thermal_critical_delta=7000" in r and "thermal_fast_up_step=8" in r and "thermal_critical_up_step=12" in r and "emergency_temperature_handoff" in r\nc=CARD.read_text(encoding="utf-8"); assert "Źródło: profil CPU/OC" in c and "niezależne od bieżącego wydania" in c\nprint("AI bucket qualification v4 / thermal fast path / restart provenance: PASS")\n''', encoding="utf-8")

workflow = ROOT / ".github" / "workflows" / "validate.yml"
replace_once(workflow, '      - name: Check whitespace errors\n', '      - name: Test AI bucket-aware qualification and thermal fast path\n        run: python scripts/test_ai_bucket_qualification_v4.py\n\n      - name: Check whitespace errors\n')

print("Prepared SBC5 3.1.7 source changes")
