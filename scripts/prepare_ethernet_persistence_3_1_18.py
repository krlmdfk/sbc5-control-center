#!/usr/bin/env python3
"""Prepare SBC5 3.1.18 Ethernet persistence and runtime profile semantics.

This one-shot, idempotent source preparer fixes two regressions observed in 3.1.17:
1. EEE UI state was stored only in /data/options.json, which Supervisor can recreate
   from native add-on defaults after a host reboot.
2. custom1 + runtime=custom + max_state=100 under Adaptive PWM was incorrectly
   reported as profile_mismatch / pending_host_reboot.

The preparer edits the authoritative sources, while existing CI tests validate the
resulting runtime and release surfaces.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"


def replace_once(path: Path, old: str, new: str, marker: str) -> None:
    text = path.read_text(encoding="utf-8")
    if marker in text:
        return
    if old not in text:
        raise SystemExit(f"Expected fragment missing in {path}: {old[:140]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_config_ui() -> None:
    path = APP / "config_ui.py"
    text = path.read_text(encoding="utf-8")

    if "ETHERNET_STATE_SCHEMA=1" not in text:
        old = "GPU_STATE = Path('/data/gpu_profile_state.json')\nGPU_STATE_SCHEMA = 1\n"
        new = old + "ETHERNET_STATE = Path('/data/ethernet_settings.json')\nETHERNET_STATE_SCHEMA=1\nETHERNET_KEYS=('ethernet_eee_mode','ethernet_health_monitor_enabled','ethernet_flap_window_minutes','ethernet_flap_degraded_threshold')\n"
        if old not in text:
            raise SystemExit("config_ui Ethernet state constant insertion point missing")
        text = text.replace(old, new, 1)

    marker = "def persist_ethernet_state(options, source='config_ui', explicit=True):"
    if marker not in text:
        anchor = "def read_options():\n"
        block = '''def read_ethernet_state():
    try:
        st=json.loads(ETHERNET_STATE.read_text()) if ETHERNET_STATE.exists() else {}
        if not isinstance(st,dict) or int(st.get('schema',0)) != ETHERNET_STATE_SCHEMA: return {}
        if str(st.get('ethernet_eee_mode','')).lower() not in ('auto','off'): return {}
        return st
    except Exception:
        return {}

def persist_ethernet_state(options, source='config_ui', explicit=True):
    mode=str(options.get('ethernet_eee_mode','auto')).strip().lower()
    if mode not in ('auto','off'): mode='auto'
    try: window=max(1,min(1440,int(options.get('ethernet_flap_window_minutes',60))))
    except Exception: window=60
    try: threshold=max(1,min(50,int(options.get('ethernet_flap_degraded_threshold',3))))
    except Exception: threshold=3
    state={
        'schema':ETHERNET_STATE_SCHEMA,
        'ethernet_eee_mode':mode,
        'ethernet_health_monitor_enabled':bool(options.get('ethernet_health_monitor_enabled',True)),
        'ethernet_flap_window_minutes':window,
        'ethernet_flap_degraded_threshold':threshold,
        'source':source,
        'explicit':bool(explicit),
        'updated':time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    _atomic_json_write(ETHERNET_STATE,state)
    return state

'''
        if anchor not in text:
            raise SystemExit("config_ui read_options insertion point missing")
        text = text.replace(anchor, block + anchor, 1)

    if "# v3.1.18: persistent Ethernet/EEE state wins" not in text:
        old = "        if out['section_gpu_enabled']:\n            out.setdefault('config_txt_manager',{})['enabled']=True\n    return out\n"
        new = "        if out['section_gpu_enabled']:\n            out.setdefault('config_txt_manager',{})['enabled']=True\n    # v3.1.18: persistent Ethernet/EEE state wins over a Supervisor-restored default snapshot.\n    est=read_ethernet_state()\n    if est:\n        for key in ETHERNET_KEYS:\n            if key in est: out[key]=copy.deepcopy(est[key])\n    return out\n"
        if old not in text:
            raise SystemExit("config_ui persistent Ethernet read overlay insertion point missing")
        text = text.replace(old, new, 1)

    if "persist_ethernet_state(o,source='config_ui',explicit=True)" not in text:
        old = "                persist_cpu_state(o,source='config_ui',explicit=True)\n                persist_gpu_state(o,source='config_ui',explicit=True)\n                RELOAD.write_text(str(int(time.time())))\n"
        new = "                persist_cpu_state(o,source='config_ui',explicit=True)\n                persist_gpu_state(o,source='config_ui',explicit=True)\n                persist_ethernet_state(o,source='config_ui',explicit=True)\n                RELOAD.write_text(str(int(time.time())))\n"
        if old not in text:
            raise SystemExit("config_ui save persistence insertion point missing")
        text = text.replace(old, new, 1)

    if "if sec=='ethernet': persist_ethernet_state" not in text:
        old = "                if sec=='cpu': persist_cpu_state(o,source='config_ui_reset',explicit=True)\n                if sec=='gpu': persist_gpu_state(o,source='config_ui_reset',explicit=True)\n                RELOAD.write_text(str(int(time.time())))\n"
        new = "                if sec=='cpu': persist_cpu_state(o,source='config_ui_reset',explicit=True)\n                if sec=='gpu': persist_gpu_state(o,source='config_ui_reset',explicit=True)\n                if sec=='ethernet': persist_ethernet_state(o,source='config_ui_reset',explicit=True)\n                RELOAD.write_text(str(int(time.time())))\n"
        if old not in text:
            raise SystemExit("config_ui reset persistence insertion point missing")
        text = text.replace(old, new, 1)

    path.write_text(text, encoding="utf-8")


def patch_ethernet_guard() -> None:
    path = APP / "ethernet_guard.py"
    text = path.read_text(encoding="utf-8")

    if 'SETTINGS_PATH = Path("/data/ethernet_settings.json")' not in text:
        old = 'OPTIONS_PATH = Path("/data/options.json")\nSTATE_DATA_PATH = Path("/data/ethernet_health.json")\n'
        new = 'OPTIONS_PATH = Path("/data/options.json")\nSETTINGS_PATH = Path("/data/ethernet_settings.json")\nSETTINGS_SCHEMA = 1\nSTATE_DATA_PATH = Path("/data/ethernet_health.json")\n'
        if old not in text:
            raise SystemExit("ethernet_guard settings constant insertion point missing")
        text = text.replace(old, new, 1)

    if "def read_persistent_settings() -> dict:" not in text:
        anchor = "def load_options() -> dict:\n"
        block = '''def read_persistent_settings() -> dict:
    state = read_json(SETTINGS_PATH, {})
    if not isinstance(state, dict) or int(state.get("schema", 0) or 0) != SETTINGS_SCHEMA:
        return {}
    mode = str(state.get("ethernet_eee_mode", "")).strip().lower()
    if mode not in {"auto", "off"}:
        return {}
    return state


def seed_persistent_settings(raw: dict) -> dict:
    mode = str(raw.get("ethernet_eee_mode", "auto")).strip().lower()
    if mode not in {"auto", "off"}:
        mode = "auto"
    try:
        window = min(1440, max(1, int(raw.get("ethernet_flap_window_minutes", 60))))
    except (TypeError, ValueError):
        window = 60
    try:
        threshold = min(50, max(1, int(raw.get("ethernet_flap_degraded_threshold", 3))))
    except (TypeError, ValueError):
        threshold = 3
    state = {
        "schema": SETTINGS_SCHEMA,
        "ethernet_eee_mode": mode,
        "ethernet_health_monitor_enabled": bool(raw.get("ethernet_health_monitor_enabled", True)),
        "ethernet_flap_window_minutes": window,
        "ethernet_flap_degraded_threshold": threshold,
        "source": "guard_initial_seed",
        "updated": utc_now(),
    }
    try:
        atomic_json_write(SETTINGS_PATH, state)
    except OSError as exc:
        log(f"persistent settings seed failed: {exc}")
    return state


'''
        if anchor not in text:
            raise SystemExit("ethernet_guard load_options insertion point missing")
        text = text.replace(anchor, block + anchor, 1)

    if "persistent = read_persistent_settings()" not in text:
        old = "    out = dict(DEFAULTS)\n    out.update({k: raw.get(k, v) for k, v in DEFAULTS.items()})\n\n    mode = str(out.get(\"ethernet_eee_mode\", \"auto\")).strip().lower()\n"
        new = "    out = dict(DEFAULTS)\n    out.update({k: raw.get(k, v) for k, v in DEFAULTS.items()})\n    # v3.1.18: /data/ethernet_settings.json is the canonical requested state.\n    # Supervisor may recreate options.json from schema defaults after a host reboot.\n    persistent = read_persistent_settings()\n    if not persistent:\n        persistent = seed_persistent_settings(out)\n    for key in DEFAULTS:\n        if key in persistent:\n            out[key] = persistent[key]\n\n    mode = str(out.get(\"ethernet_eee_mode\", \"auto\")).strip().lower()\n"
        if old not in text:
            raise SystemExit("ethernet_guard persistent overlay insertion point missing")
        text = text.replace(old, new, 1)

    # Make startup diagnostics report the actual requested state rather than a static default.
    if "persistent_state={'yes' if SETTINGS_PATH.exists() else 'no'}" not in text:
        old = '    log(f"starting v{APP_VERSION}; EEE ownership is opt-in (default=auto).")\n    previous = read_json(STATE_DATA_PATH, {})\n'
        new = '    startup_options = load_options()\n    log(f"starting v{APP_VERSION}; requested_eee={startup_options.get(\'ethernet_eee_mode\', \'auto\')}; persistent_state={\'yes\' if SETTINGS_PATH.exists() else \'no\'}.")\n    previous = read_json(STATE_DATA_PATH, {})\n'
        if old not in text:
            raise SystemExit("ethernet_guard startup log insertion point missing")
        text = text.replace(old, new, 1)

    # Correct status semantics for both directions of a boot-only EEE change.
    old = '''        eee_status = "auto"
        if mode == "off":
            if not boot_result.get("configured_off"):
                eee_status = "off_error"
            elif pending:
                eee_status = "off_pending_restart"
            else:
                eee_status = "off_configured"
        elif boot_result.get("external_eee_off"):
            eee_status = "off_external"
'''
    new = '''        eee_status = "auto"
        if mode == "off":
            if not boot_result.get("configured_off"):
                eee_status = "off_error"
            elif pending:
                eee_status = "off_pending_restart"
            else:
                eee_status = "off_active"
        elif pending:
            eee_status = "auto_pending_restart"
        elif boot_result.get("external_eee_off"):
            eee_status = "off_external"
'''
    if "eee_status = \"off_active\"" not in text:
        if old not in text:
            raise SystemExit("ethernet_guard status semantics insertion point missing")
        text = text.replace(old, new, 1)

    if '"settings_source": "persistent" if read_persistent_settings() else "options",' not in text:
        old = '            "eee_requested": mode,\n            "eee_status": eee_status,\n'
        new = '            "eee_requested": mode,\n            "eee_status": eee_status,\n            "settings_source": "persistent" if read_persistent_settings() else "options",\n'
        if old not in text:
            raise SystemExit("ethernet_guard settings source insertion point missing")
        text = text.replace(old, new, 1)

    path.write_text(text, encoding="utf-8")


def patch_run_bootstrap() -> None:
    path = APP / "run.sh"
    text = path.read_text(encoding="utf-8")
    if "tee -a /tmp/sbc5_ethernet_guard.log" not in text:
        old = '''if [ -x "$ETHERNET_GUARD" ]; then
  "$ETHERNET_GUARD" >/tmp/sbc5_ethernet_guard.log 2>&1 &
  echo "[SBC5 ${APP_VERSION}] Ethernet Stability Guard: enabled (EEE default=auto)."
'''
        new = '''if [ -x "$ETHERNET_GUARD" ]; then
  "$ETHERNET_GUARD" > >(tee -a /tmp/sbc5_ethernet_guard.log) 2>&1 &
  echo "[SBC5 ${APP_VERSION}] Ethernet Stability Guard: enabled (persistent EEE state + end0 health)."
'''
        if old not in text:
            raise SystemExit("run.sh Ethernet guard bootstrap insertion point missing")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def patch_fan_profile_runtime_semantics() -> None:
    path = APP / "run_legacy.sh"
    text = path.read_text(encoding="utf-8")
    marker = 'activation_reason="adaptive_runtime_grid_active"'
    if marker in text:
        return
    old = '''  elif [ "$requested_code" != "$code" ]; then
    pending=true; activation_state="pending_host_reboot"; activation_reason="profile_mismatch"
    message="Profil żądany ${requested_label} nie jest jeszcze aktywny w kernelu. Wykonaj pełny restart hosta."
'''
    new = '''  elif [ "$requested_code" = "custom1" ] && [ "$code" = "custom" ] && [ "$max_state" = "100" ] && [ "$COOLING_CONTROL_MODE" = "automatic" ] && [ "$ADAPTIVE_PWM_ENABLED" = "true" ]; then
    pending=false; activation_state="active_runtime_managed"; activation_reason="adaptive_runtime_grid_active"
    message="custom1 jest aktywny: kernel udostępnia siatkę 1%, a Adaptive PWM realizuje krzywą i korektę w user-space. Restart hosta nie jest wymagany."
  elif [ "$requested_code" != "$code" ]; then
    pending=true; activation_state="pending_host_reboot"; activation_reason="profile_mismatch"
    message="Profil żądany ${requested_label} nie jest jeszcze aktywny w kernelu. Wykonaj pełny restart hosta."
'''
    if old not in text:
        raise SystemExit("run_legacy fan profile mismatch insertion point missing")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_tests() -> None:
    runtime = ROOT / "scripts" / "test_runtime_robustness.py"
    text = runtime.read_text(encoding="utf-8")
    marker = "# 3.1.18 Ethernet state persistence regression."
    if marker not in text:
        old = "assert 'chmod a+x /run.sh /run_legacy.sh' in docker\n"
        new = old + '''\n# 3.1.18 Ethernet state persistence regression.\nguard = (APP / 'ethernet_guard.py').read_text(encoding='utf-8')\nconfig_ui = (APP / 'config_ui.py').read_text(encoding='utf-8')\nassert 'SETTINGS_PATH = Path(\"/data/ethernet_settings.json\")' in guard\nassert 'persistent = read_persistent_settings()' in guard\nassert 'eee_status = \"off_active\"' in guard\nassert 'eee_status = \"auto_pending_restart\"' in guard\nassert \"ETHERNET_STATE = Path('/data/ethernet_settings.json')\" in config_ui\nassert \"persist_ethernet_state(o,source='config_ui',explicit=True)\" in config_ui\nassert 'tee -a /tmp/sbc5_ethernet_guard.log' in bootstrap\n'''
        if old not in text:
            raise SystemExit("runtime robustness test insertion point missing")
        text = text.replace(old, new, 1)
        runtime.write_text(text, encoding="utf-8")

    fan = ROOT / "scripts" / "test_fan_profile_active_slot_overlay.py"
    text = fan.read_text(encoding="utf-8")
    marker = "adaptive_runtime_grid_active"
    if marker not in text:
        old = "assert '\"$BOOT_MP/slot-B/overlays\"' in run\n"
        new = old + '''\n# 3.1.18: userspace-managed custom1 on an active 1% grid is already effective.\n# runtime=custom is the kernel's generic label and must not create a fake reboot request.\nassert 'activation_state=\"active_runtime_managed\"; activation_reason=\"adaptive_runtime_grid_active\"' in run\nassert '[ \"$requested_code\" = \"custom1\" ] && [ \"$code\" = \"custom\" ] && [ \"$max_state\" = \"100\" ]' in run\n'''
        if old not in text:
            raise SystemExit("fan profile regression test insertion point missing")
        text = text.replace(old, new, 1)
        fan.write_text(text, encoding="utf-8")


def main() -> int:
    patch_config_ui()
    patch_ethernet_guard()
    patch_run_bootstrap()
    patch_fan_profile_runtime_semantics()
    patch_tests()
    print("SBC5 3.1.18 Ethernet persistence + fan runtime semantics source preparation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
