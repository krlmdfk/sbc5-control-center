#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
CURRENT = "3.1.3"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Expected block not found in {path}: {old[:180]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_all_checked(path: Path, old: str, new: str, minimum: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count < minimum:
        raise SystemExit(f"Expected >= {minimum} occurrences in {path}, got {count}: {old!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Canonical package/version surfaces: remove the ancient 2.8.34 source.
# ---------------------------------------------------------------------------
package_files = [
    ROOT / "packages" / "sbc5_control_center.yaml",
    APP / "migration_assets" / "sbc5_control_center.yaml",
    APP / "migration_assets" / "rpi5_control_center.yaml",
]
for path in package_files:
    text = path.read_text(encoding="utf-8")
    text, n1 = re.subn(r"(?m)^(# SBC5 Control Center Package Version:)\s*\d+\.\d+\.\d+\s*$", rf"\1 {CURRENT}", text, count=1)
    text, n2 = re.subn(
        r'(?ms)(- name: SBC5 Package Version\n\s+unique_id: sbc5_package_version\n\s+icon: mdi:package-variant-closed-check\n\s+state:)\s*"\d+\.\d+\.\d+"',
        rf'\1 "{CURRENT}"',
        text,
        count=1,
    )
    if n1 != 1 or n2 != 1:
        raise SystemExit(f"Could not normalize package version markers in {path}: header={n1}, sensor={n2}")
    path.write_text(text, encoding="utf-8")

# Current-surface fallbacks that escaped old->new replacement in earlier releases.
config_ui = APP / "config_ui.py"
text = config_ui.read_text(encoding="utf-8")
text, n = re.subn(r"return ['\"]2\.8\.34['\"]", f"return '{CURRENT}'", text, count=1)
if n != 1:
    raise SystemExit("config_ui.py stale fallback not found")
config_ui.write_text(text, encoding="utf-8")

namespace_guard = APP / "namespace_native_guard.sh"
text = namespace_guard.read_text(encoding="utf-8")
text, n = re.subn(r'(?m)^VERSION="2\.8\.34"$', f'VERSION="{CURRENT}"', text, count=1)
if n != 1:
    raise SystemExit("namespace_native_guard.sh stale VERSION not found")
namespace_guard.write_text(text, encoding="utf-8")

# Make future releases normalize these surfaces by structure, not only old-version replacement.
release_prepare = ROOT / "scripts" / "release_prepare.py"
needle = '''def normalize_manifest(path: Path, version: str) -> None:\n'''
helper = '''def normalize_current_version_surfaces(version: str) -> None:\n    """Normalize current runtime/package version markers independent of release history.\n\n    A stale literal can survive generic old->new replacement indefinitely once it\n    misses one release. Keep these authoritative current-state surfaces structural.\n    """\n    package_files = [\n        ROOT / "packages" / "sbc5_control_center.yaml",\n        APP / "migration_assets" / "sbc5_control_center.yaml",\n        APP / "migration_assets" / "rpi5_control_center.yaml",\n    ]\n    for path in package_files:\n        if not path.is_file():\n            continue\n        text = path.read_text(encoding="utf-8")\n        text = re.sub(\n            r"(?m)^(# SBC5 Control Center Package Version:)\\s*\\d+\\.\\d+\\.\\d+\\s*$",\n            rf"\\1 {version}",\n            text,\n            count=1,\n        )\n        text = re.sub(\n            r'(?ms)(- name: SBC5 Package Version\\n\\s+unique_id: sbc5_package_version\\n\\s+icon: mdi:package-variant-closed-check\\n\\s+state:)\\s*"\\d+\\.\\d+\\.\\d+"',\n            rf'\\1 "{version}"',\n            text,\n            count=1,\n        )\n        path.write_text(text, encoding="utf-8")\n\n    current_literals = [\n        (APP / "namespace_native_guard.sh", r'(?m)^VERSION="\\d+\\.\\d+\\.\\d+"$', f'VERSION="{version}"'),\n        (APP / "config_ui.py", r"return ['\\\"]\\d+\\.\\d+\\.\\d+['\\\"]", f"return '{version}'"),\n    ]\n    for path, pattern, replacement in current_literals:\n        if not path.is_file():\n            continue\n        text = path.read_text(encoding="utf-8")\n        text, count = re.subn(pattern, replacement, text, count=1)\n        if count != 1:\n            raise SystemExit(f"Could not normalize current version surface: {path}")\n        path.write_text(text, encoding="utf-8")\n\n\n'''
replace_once(release_prepare, needle, helper + needle)
replace_once(
    release_prepare,
    '''    for path in VERSIONED_TEXT_FILES:\n        replace_current_version(path, old, new)\n\n    canonical = ROOT / "custom_components" / DOMAIN\n''',
    '''    for path in VERSIONED_TEXT_FILES:\n        replace_current_version(path, old, new)\n    normalize_current_version_surfaces(new)\n\n    canonical = ROOT / "custom_components" / DOMAIN\n''',
)

# ---------------------------------------------------------------------------
# 2. Restart Manager: reconcile legacy/generic CPU marker only with hard proof.
# ---------------------------------------------------------------------------
run = APP / "run_legacy.sh"
old = '''  if [ "$saved_boot" = "$CURRENT_BOOT_ID" ] && [ "$verification_failed" != "true" ]; then\n    if [ "$scope" = "cpu_profile" ]; then\n      profile="$(jq -r '.expected_profile // "factory"' "$RESTART_STATE_FILE" 2>/dev/null || echo factory)"\n      expected_arm="$(jq -r 'if .expected_arm_freq == null then "" else (.expected_arm_freq|tostring) end' "$RESTART_STATE_FILE" 2>/dev/null || true)"\n      if { [ "$profile" = "factory" ] || [[ "$expected_arm" =~ ^[0-9]+$ ]]; } && cpu_profile_verify_after_boot "$profile" "$expected_arm"; then\n        log "Restart Manager: bieżący boot już spełnia oczekiwany profil CPU/OC — usuwam osierocony marker restart=host."\n        rm -f "$RESTART_STATE_FILE"\n      fi\n    fi\n    return 0\n  fi\n'''
new = '''  if [ "$saved_boot" = "$CURRENT_BOOT_ID" ] && [ "$verification_failed" != "true" ]; then\n    if [ "$scope" = "cpu_profile" ]; then\n      profile="$(jq -r '.expected_profile // "factory"' "$RESTART_STATE_FILE" 2>/dev/null || echo factory)"\n      expected_arm="$(jq -r 'if .expected_arm_freq == null then "" else (.expected_arm_freq|tostring) end' "$RESTART_STATE_FILE" 2>/dev/null || true)"\n      if { [ "$profile" = "factory" ] || [[ "$expected_arm" =~ ^[0-9]+$ ]]; } && cpu_profile_verify_after_boot "$profile" "$expected_arm"; then\n        log "Restart Manager: bieżący boot już spełnia oczekiwany profil CPU/OC — usuwam osierocony marker restart=host."\n        rm -f "$RESTART_STATE_FILE"\n        native_restart_repair_clear || true\n      fi\n    elif [ "$scope" = "generic" ] || [ -z "$scope" ]; then\n      # 3.1.4 legacy reconciliation: old CPU markers did not carry scope/expected\n      # fields. Infer CPU ownership only from an explicit CPU/OC reason, then use\n      # the persistent requested profile plus Boot Verification as hard proof.\n      local legacy_reason requested_profile requested_arm\n      legacy_reason="$(jq -r '.reason // empty' "$RESTART_STATE_FILE" 2>/dev/null || true)"\n      case "${legacy_reason,,}" in\n        *"cpu/oc"*|*"profil cpu"*|*"arm_freq"*|*"taktowanie cpu"*)\n          requested_profile="$(cpu_profile_requested_profile 2>/dev/null || echo factory)"\n          requested_arm="$(cpu_profile_expected_arm_freq "$requested_profile" 2>/dev/null || true)"\n          if { [ "$requested_profile" = "factory" ] || [[ "$requested_arm" =~ ^[0-9]+$ ]]; } \\\n             && cpu_profile_verify_after_boot "$requested_profile" "$requested_arm"; then\n            log "Restart Manager: legacy marker host dotyczył CPU/OC, a zapisany i aktywny profil są już zgodne — zamykam osierocone żądanie."\n            rm -f "$RESTART_STATE_FILE"\n            native_restart_repair_clear || true\n          fi\n          ;;\n      esac\n    fi\n    return 0\n  fi\n'''
replace_once(run, old, new)

# ---------------------------------------------------------------------------
# 3. Thermal Predictor confidence: accuracy must materially affect confidence.
# ---------------------------------------------------------------------------
ai = APP / "ai_cooling.py"
old = '''    accuracy_factor = 0.55 if avg_mae is None else _clamp(1.0 - avg_mae / 4.0, 0.20, 1.0)\n    confidence = int(round(_clamp(20.0 + 30.0 * span_factor + 20.0 * point_factor + 20.0 * maturity + 10.0 * accuracy_factor, 0.0, 97.0)))\n\n    state = {\n'''
new = '''    # 3.1.4: confidence is a quality score, not only a data-volume score.\n    # Prediction error now carries 35% of the result; a mature model with MAE\n    # around 2-3 C can no longer advertise >90% confidence. Observe-only remains.\n    accuracy_factor = 0.35 if avg_mae is None else _clamp(1.0 - avg_mae / 3.0, 0.0, 1.0)\n    confidence = int(round(_clamp(100.0 * (\n        0.25 * span_factor + 0.15 * point_factor + 0.25 * maturity + 0.35 * accuracy_factor\n    ), 0.0, 97.0)))\n    if avg_mae is None:\n        quality_state = "learning"\n    elif avg_mae <= 0.75:\n        quality_state = "excellent"\n    elif avg_mae <= 1.25:\n        quality_state = "good"\n    elif avg_mae <= 2.0:\n        quality_state = "fair"\n    elif avg_mae <= 3.0:\n        quality_state = "weak"\n    else:\n        quality_state = "poor"\n\n    state = {\n'''
replace_once(ai, old, new)
replace_once(
    ai,
    '''        "confidence_percent": confidence,\n        "mae_ema_c": {k: round(_num(v), 3) for k, v in mae.items()},\n''',
    '''        "confidence_percent": confidence,\n        "quality_state": quality_state,\n        "mae_ema_c": {k: round(_num(v), 3) for k, v in mae.items()},\n''',
)

# Native quality sensor (bundled canonical integration); HACS repo will mirror it.
sensor = ROOT / "custom_components" / "sbc5_control_center" / "sensor.py"
replace_once(
    sensor,
    '''    SensorSpec(unique_id="sbc5_ai_thermal_predictor_confidence", name="SBC5 AI Thermal Predictor Confidence", value_fn=lambda d: _predictor_number(d, "confidence_percent"), icon="mdi:brain", unit=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),\n''',
    '''    SensorSpec(unique_id="sbc5_ai_thermal_predictor_confidence", name="SBC5 AI Thermal Predictor Confidence", value_fn=lambda d: _predictor_number(d, "confidence_percent"), icon="mdi:brain", unit=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),\n    SensorSpec(unique_id="sbc5_ai_thermal_predictor_quality", name="SBC5 AI Thermal Predictor Quality", value_fn=lambda d: d.thermal_predictor.get("quality_state") or None, icon="mdi:brain-check-outline"),\n''',
)

# ---------------------------------------------------------------------------
# 4. Lovelace resilience after HA Core restart.
# ---------------------------------------------------------------------------
card = ROOT / "dashboard" / "sbc5_control_center_diagnostics_card.yaml"
text = card.read_text(encoding="utf-8")
# Every independent template that reads the transient REST compatibility entity
# gets a fallback from the persistent app telemetry relay.
old_ps = "{% set ps = states('sensor.sbc5_platform_compatibility') %}"
new_ps = "{% set pc = state_attr('sensor.sbc5_control_center_host_telemetry','platform_compatibility') or {} %}\n      {% set direct = states('sensor.sbc5_platform_compatibility') %}\n      {% set ps = direct if direct not in ['unknown','unavailable','none',''] else pc.get('state','unknown') %}"
count = text.count(old_ps)
if count < 3:
    raise SystemExit(f"Expected >=3 platform state templates, got {count}")
text = text.replace(old_ps, new_ps)
old_secondary = '''    secondary: >-\n      Core {{ state_attr('sensor.sbc5_platform_compatibility','installed_core') | default('—', true) }}\n      (min. {{ state_attr('sensor.sbc5_platform_compatibility','minimum_core') | default('2026.10.1', true) }}) · HA OS {{ state_attr('sensor.sbc5_platform_compatibility','installed_haos') | default('—', true) }}\n      (min. {{ state_attr('sensor.sbc5_platform_compatibility','minimum_haos') | default('18.3', true) }})\n'''
new_secondary = '''    secondary: >-\n      {% set pc = state_attr('sensor.sbc5_control_center_host_telemetry','platform_compatibility') or {} %}\n      Core {{ state_attr('sensor.sbc5_platform_compatibility','installed_core') | default(pc.get('installed_core','—'), true) }}\n      (min. {{ state_attr('sensor.sbc5_platform_compatibility','minimum_core') | default(pc.get('minimum_core','2026.10.1'), true) }}) · HA OS {{ state_attr('sensor.sbc5_platform_compatibility','installed_haos') | default(pc.get('installed_haos','—'), true) }}\n      (min. {{ state_attr('sensor.sbc5_platform_compatibility','minimum_haos') | default(pc.get('minimum_haos','18.3'), true) }})\n'''
if old_secondary not in text:
    raise SystemExit("Platform secondary block not found")
text = text.replace(old_secondary, new_secondary, 1)
# Make predictor quality visible without changing control behavior.
text = text.replace(
    "MAE śr. {{ states('sensor.sbc5_ai_thermal_predictor_mae') }} °C\n                · trend",
    "{{ states('sensor.sbc5_ai_thermal_predictor_quality') }} · MAE śr. {{ states('sensor.sbc5_ai_thermal_predictor_mae') }} °C\n                · trend",
    1,
)
# Transient update REST entity should not make the main card look broken when the
# package/native version is known.
text = text.replace(
    "Status aktualizacji chwilowo niedostępny",
    "Wersja {{ states('sensor.sbc5_package_version') }} · oczekiwanie na synchronizację statusu",
)
card.write_text(text, encoding="utf-8")

update_card = ROOT / "dashboard" / "update_status_card.yaml"
text = update_card.read_text(encoding="utf-8")
text = text.replace(
    "Status aktualizacji chwilowo niedostępny",
    "Wersja {{ installed }} · oczekiwanie na synchronizację statusu",
    1,
)
update_card.write_text(text, encoding="utf-8")

print("Applied SBC5 3.1.4 runtime consistency patch")
