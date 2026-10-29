#!/usr/bin/env python3
"""One-shot deterministic source preparation for SBC5 3.1.17 Ethernet stability.

The script edits large generated/runtime surfaces in-place so the release branch can
be prepared and validated by GitHub Actions without hand-editing minified UI files.
It is intentionally idempotent.
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
CANON = ROOT / "custom_components" / "sbc5_control_center"
BRIDGE = APP / "bridge"


def replace_once(path: Path, old: str, new: str, *, marker: str | None = None) -> None:
    text = path.read_text(encoding="utf-8")
    if marker and marker in text:
        return
    if old not in text:
        raise SystemExit(f"Expected source fragment not found in {path}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_guard() -> None:
    path = APP / "ethernet_guard.py"
    marker = "Conflicting external dtparam=eee=on"
    text = path.read_text(encoding="utf-8")
    if marker in text:
        return
    old = '''    desired, external_off, external_on = desired_boot_text(current, mode)\n    result["external_eee_off"] = external_off\n    result["external_eee_on"] = external_on\n\n    if desired != current:\n'''
    new = '''    external_off, external_on = external_eee_state(current)\n    result["external_eee_off"] = external_off\n    result["external_eee_on"] = external_on\n    if mode == "off" and external_on and not external_off:\n        result["error"] = "Conflicting external dtparam=eee=on; SBC5 left config.txt unchanged"\n        log(result["error"])\n        return result\n    if mode == "off" and external_on and external_off:\n        result["error"] = "Conflicting external dtparam=eee=on/off entries; SBC5 left config.txt unchanged"\n        log(result["error"])\n        return result\n\n    desired, external_off, external_on = desired_boot_text(current, mode)\n\n    if desired != current:\n'''
    if old not in text:
        raise SystemExit("ethernet_guard conflict insertion point missing")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_config_ui_py() -> None:
    path = APP / "config_ui.py"
    text = path.read_text(encoding="utf-8")
    if "'ethernet_eee_mode':'auto'" not in text:
        old = "  'post_update_restart_prompt':True,'native_restart_repair':True,\n"
        new = old + "  'ethernet_eee_mode':'auto','ethernet_health_monitor_enabled':True,'ethernet_flap_window_minutes':60,'ethernet_flap_degraded_threshold':3,\n"
        if old not in text:
            raise SystemExit("config_ui DEFAULTS insertion point missing")
        text = text.replace(old, new, 1)
    if "'ethernet':['ethernet_eee_mode'" not in text:
        old = " 'safety':['restart_policy','pre_restart_config_check','restart_notice_on_start','post_update_restart_prompt','native_restart_repair'],\n"
        new = old + " 'ethernet':['ethernet_eee_mode','ethernet_health_monitor_enabled','ethernet_flap_window_minutes','ethernet_flap_degraded_threshold'],\n"
        if old not in text:
            raise SystemExit("config_ui SECTION_KEYS insertion point missing")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def patch_config_ui_html() -> None:
    path = APP / "config_ui" / "index.html"
    text = path.read_text(encoding="utf-8")
    marker = "Ethernet / EEE Stability"
    if marker in text:
        return
    anchor = "['telemetry','Telemetria rozszerzona','Wielordzeniowe zbieranie diagnostyki.','telemetry',[['multicore_telemetry_enabled','Multicore telemetry','bool'],['multicore_workers','Workers','select:auto|1|2|3|4']],true],"
    entry = "['ethernet','Ethernet / EEE Stability','Stabilność end0 na Raspberry Pi 5. EEE=off zapisuje dtparam=eee=off z backupem i wymaga pełnego restartu hosta.','ethernet',[['ethernet_eee_mode','Energy Efficient Ethernet','select:auto|off'],['ethernet_health_monitor_enabled','Monitoruj link end0','bool'],['ethernet_flap_window_minutes','Okno flappingu (min)','number'],['ethernet_flap_degraded_threshold','Próg DEGRADED','number']],false],\n"
    if anchor not in text:
        raise SystemExit("config_ui HTML specs insertion point missing")
    path.write_text(text.replace(anchor, entry + anchor, 1), encoding="utf-8")


def patch_coordinator(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "ethernet_health: dict[str, Any]" in text:
        return
    text = text.replace("from dataclasses import dataclass\n", "from dataclasses import dataclass\nimport json\nfrom pathlib import Path\n", 1)
    old = "    thermal_predictor: dict[str, Any]\n\n\ndef _telemetry_from_host_relay"
    new = "    thermal_predictor: dict[str, Any]\n    ethernet_health: dict[str, Any]\n\n\ndef _read_ethernet_health(hass: HomeAssistant) -> dict[str, Any]:\n    path = Path(hass.config.path(\"sbc5_control_center/ethernet_health.json\"))\n    try:\n        data = json.loads(path.read_text(encoding=\"utf-8\"))\n    except (OSError, json.JSONDecodeError, TypeError):\n        return {}\n    return data if isinstance(data, dict) else {}\n\n\ndef _telemetry_from_host_relay"
    if old not in text:
        raise SystemExit(f"coordinator dataclass insertion point missing: {path}")
    text = text.replace(old, new, 1)
    old = "        app_update = AppUpdateInfo(\n"
    new = "        ethernet_health = await self.hass.async_add_executor_job(_read_ethernet_health, self.hass)\n\n        app_update = AppUpdateInfo(\n"
    if old not in text:
        raise SystemExit(f"coordinator update insertion point missing: {path}")
    text = text.replace(old, new, 1)
    old = "            telemetry=telemetry, app_update=app_update, thermal_predictor=thermal_predictor\n"
    new = "            telemetry=telemetry, app_update=app_update, thermal_predictor=thermal_predictor, ethernet_health=ethernet_health\n"
    if old not in text:
        raise SystemExit(f"coordinator return insertion point missing: {path}")
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def patch_sensor(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if 'unique_id="sbc5_ethernet_health"' in text:
        return
    anchor = '    SensorSpec(unique_id="sbc5_network_mac", name="SBC5 Network MAC", value_fn=lambda d: d.telemetry.network_mac or None, icon="mdi:lan-connect"),\n'
    entry = (
        '    SensorSpec(unique_id="sbc5_ethernet_health", name="SBC5 Ethernet Health", value_fn=lambda d: d.ethernet_health.get("health") or None, icon="mdi:ethernet"),\n'
        '    SensorSpec(unique_id="sbc5_ethernet_link_flaps", name="SBC5 Ethernet Link Flaps", value_fn=lambda d: d.ethernet_health.get("flap_count_window"), icon="mdi:swap-horizontal-bold", state_class=SensorStateClass.MEASUREMENT),\n'
        '    SensorSpec(unique_id="sbc5_ethernet_eee_status", name="SBC5 Ethernet EEE Status", value_fn=lambda d: d.ethernet_health.get("eee_status") or None, icon="mdi:leaf-off"),\n'
    )
    if anchor not in text:
        raise SystemExit(f"sensor insertion point missing: {path}")
    path.write_text(text.replace(anchor, entry + anchor, 1), encoding="utf-8")


def patch_validation_workflow() -> None:
    path = ROOT / ".github" / "workflows" / "validate.yml"
    text = path.read_text(encoding="utf-8")
    if "Test Ethernet EEE stability guard" in text:
        return
    anchor = "      - name: Test migration profile guard\n        run: python scripts/test_migration_profile_guard.py\n"
    entry = anchor + "\n      - name: Test Ethernet EEE stability guard\n        run: python scripts/test_ethernet_stability.py\n"
    if anchor not in text:
        raise SystemExit("validate workflow insertion point missing")
    path.write_text(text.replace(anchor, entry, 1), encoding="utf-8")


def main() -> int:
    patch_guard()
    patch_config_ui_py()
    patch_config_ui_html()
    for root in (CANON, BRIDGE):
        patch_coordinator(root / "coordinator.py")
        patch_sensor(root / "sensor.py")
    patch_validation_workflow()

    # The canonical and packaged integration trees must remain byte-identical.
    for rel in ("coordinator.py", "sensor.py"):
        if (CANON / rel).read_bytes() != (BRIDGE / rel).read_bytes():
            raise SystemExit(f"Bridge parity failed for {rel}")

    print("Ethernet stability source preparation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
