#!/usr/bin/env python3
from pathlib import Path
import json
import re


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"missing expected block in {path}: {old[:100]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_all(path: str, old: str, new: str) -> int:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if not count:
        return 0
    p.write_text(text.replace(old, new), encoding="utf-8")
    return count

# 1) Ingress template endpoints must return runtime-versioned cards, not raw stale JSON.
replace_once(
    "local_apps/sbc5_control_center/config_ui.py",
    "import json, os, tempfile, time, copy\n",
    "import json, os, tempfile, time, copy, re\n",
)
replace_once(
    "local_apps/sbc5_control_center/config_ui.py",
    "def current_update_card_json_path():\n    return UPDATE_CARD_JSON_OVERRIDE if UPDATE_CARD_JSON_OVERRIDE.is_file() else UPDATE_CARD_JSON\n\nOPTIONS = Path('/data/options.json')\n",
    '''def current_update_card_json_path():\n    return UPDATE_CARD_JSON_OVERRIDE if UPDATE_CARD_JSON_OVERRIDE.is_file() else UPDATE_CARD_JSON\n\ndef _runtime_versioned_card(card):\n    \"\"\"Normalize embedded card markers to the release Card UI version.\n\n    Browser-session Lovelace sync uses these template endpoints directly.  Returning\n    raw packaged JSON previously allowed an old Update Card marker (2.8.34) to be\n    written back even while the App and Card UI were already 3.1.1.\n    \"\"\"\n    version = current_card_ui_version()\n    def walk(value):\n        if isinstance(value, str):\n            value = re.sub(r'Card UI v\\d+\\.\\d+\\.\\d+', f'Card UI v{version}', value)\n            value = re.sub(r'Update Card v\\d+\\.\\d+\\.\\d+', f'Update Card v{version}', value)\n            value = re.sub(r'SBC5CC \\d+\\.\\d+\\.\\d+', f'SBC5CC {version}', value)\n            return value\n        if isinstance(value, list):\n            return [walk(v) for v in value]\n        if isinstance(value, dict):\n            return {k: walk(v) for k, v in value.items()}\n        return value\n    return walk(card)\n\nOPTIONS = Path('/data/options.json')\n''',
)
replace_once(
    "local_apps/sbc5_control_center/config_ui.py",
    "                card=json.loads(current_card_json_path().read_text(encoding='utf-8'))\n                self.send_json({'ok':True,'packaged_version':current_card_ui_version(),'card':card}); return\n",
    "                card=_runtime_versioned_card(json.loads(current_card_json_path().read_text(encoding='utf-8')))\n                self.send_json({'ok':True,'packaged_version':current_card_ui_version(),'card':card}); return\n",
)
replace_once(
    "local_apps/sbc5_control_center/config_ui.py",
    "                card=json.loads(current_update_card_json_path().read_text(encoding='utf-8'))\n                self.send_json({'ok':True,'packaged_version':current_card_ui_version(),'card':card}); return\n",
    "                card=_runtime_versioned_card(json.loads(current_update_card_json_path().read_text(encoding='utf-8')))\n                self.send_json({'ok':True,'packaged_version':current_card_ui_version(),'card':card}); return\n",
)

# Keep the backend sync normalizer consistent with browser-session sync.
replace_once(
    "local_apps/sbc5_control_center/dashboard_sync.py",
    "            value = re.sub(r'Card UI v\\d+\\.\\d+\\.\\d+', f'Card UI v{version}', value)\n            value = re.sub(r'SBC5CC \\d+\\.\\d+\\.\\d+', f'SBC5CC {version}', value)\n",
    "            value = re.sub(r'Card UI v\\d+\\.\\d+\\.\\d+', f'Card UI v{version}', value)\n            value = re.sub(r'Update Card v\\d+\\.\\d+\\.\\d+', f'Update Card v{version}', value)\n            value = re.sub(r'SBC5CC \\d+\\.\\d+\\.\\d+', f'SBC5CC {version}', value)\n",
)

# Canonical update card had a hard-coded historical 2.8.34 marker.
for path in ("dashboard/update_status_card.yaml", "local_apps/sbc5_control_center/update_status_card.json"):
    replace_all(path, "2.8.34", "3.1.2")

# 2) Use the host network namespace for device identity MAC.  Container MACs are
# ephemeral and caused Home Assistant Device Registry to accumulate many addresses.
old_mac = '''  SYS_NETWORK_MAC=""\n  if [ -n "${SYS_NET_IFACE:-}" ] && [ -r "/sys/class/net/$SYS_NET_IFACE/address" ]; then\n    SYS_NETWORK_MAC="$(tr '[:upper:]' '[:lower:]' < "/sys/class/net/$SYS_NET_IFACE/address" 2>/dev/null | tr -d '\\r\\n' || true)"\n  fi\n'''
new_mac = '''  # Device identity must come from the Raspberry Pi host, never from the\n  # App/container network namespace. Container veth/MAC addresses can change after\n  # upgrades and caused Device Registry to retain a growing list of stale MACs.\n  SYS_NETWORK_MAC=""\n  local host_net_iface="" host_mac_path="" host_mac="" ni=""\n  if command -v nsenter >/dev/null 2>&1 && command -v ip >/dev/null 2>&1; then\n    host_net_iface="$(nsenter -t 1 -n ip route 2>/dev/null | awk '/^default/ {print $5; exit}' || true)"\n  fi\n  if [ -z "$host_net_iface" ] && [ -d /proc/1/root/sys/class/net ]; then\n    for ni in /proc/1/root/sys/class/net/*; do\n      [ -e "$ni" ] || continue\n      [ "${ni##*/}" = "lo" ] && continue\n      # Prefer a real host device; skip virtual bridges/veth/tunnels.\n      [ -e "$ni/device" ] || continue\n      if [ -r "$ni/operstate" ] && [ "$(cat "$ni/operstate" 2>/dev/null || true)" = "up" ]; then\n        host_net_iface="${ni##*/}"; break\n      fi\n      [ -n "$host_net_iface" ] || host_net_iface="${ni##*/}"\n    done\n  fi\n  if [ -n "$host_net_iface" ]; then\n    host_mac_path="/proc/1/root/sys/class/net/$host_net_iface/address"\n    if [ -r "$host_mac_path" ]; then\n      host_mac="$(tr '[:upper:]' '[:lower:]' < "$host_mac_path" 2>/dev/null | tr -d '\\r\\n' || true)"\n      if [[ "$host_mac" =~ ^([0-9a-f]{2}:){5}[0-9a-f]{2}$ ]] && [ "$host_mac" != "00:00:00:00:00:00" ]; then\n        SYS_NETWORK_MAC="$host_mac"\n      fi\n    fi\n  fi\n'''
replace_once("local_apps/sbc5_control_center/run_legacy.sh", old_mac, new_mac)

# 3) Card predictor tiles should fall back directly to the already-existing AI
# runtime relay. This makes the forecast visible even before HA has created the
# recorder/native sensor entities after an integration reload.
yaml = Path("dashboard/sbc5_control_center_diagnostics_card.yaml")
text = yaml.read_text(encoding="utf-8")
for horizon in (30, 60, 120):
    old = f'''                {{% set v = states('sensor.sbc5_ai_thermal_forecast_{horizon}s') %}}\n                {{{{ v if v not in ['unknown','unavailable','none',''] else '—' }}}} °C'''
    new = f'''                {{% set v = states('sensor.sbc5_ai_thermal_forecast_{horizon}s') %}}\n                {{% if v not in ['unknown','unavailable','none',''] %}}\n                  {{{{ v }}}} °C\n                {{% else %}}\n                  {{% set ai = state_attr('sensor.sbc5_control_center_ai_runtime','ai_cooling') %}}\n                  {{% set p = ai.get('thermal_predictor', {{}}) if ai is mapping else {{}} %}}\n                  {{{{ p.get('forecast_{horizon}s_c', '—') }}}} °C\n                {{% endif %}}'''
    if old not in text:
        raise SystemExit(f"missing predictor card block {horizon}s")
    text = text.replace(old, new, 1)
old = '''                {% set v = states('sensor.sbc5_ai_thermal_predictor_confidence') %}\n                {{ v if v not in ['unknown','unavailable','none',''] else '—' }}% · observe-only'''
new = '''                {% set v = states('sensor.sbc5_ai_thermal_predictor_confidence') %}\n                {% if v not in ['unknown','unavailable','none',''] %}\n                  {{ v }}% · observe-only\n                {% else %}\n                  {% set ai = state_attr('sensor.sbc5_control_center_ai_runtime','ai_cooling') %}\n                  {% set p = ai.get('thermal_predictor', {}) if ai is mapping else {} %}\n                  {{ p.get('confidence_percent', '—') }}% · observe-only\n                {% endif %}'''
if old not in text:
    raise SystemExit("missing predictor confidence card block")
text = text.replace(old, new, 1)
yaml.write_text(text, encoding="utf-8")

# 4) Remove the temporary package-owned predictor sensors. 3.1.2 moves their
# ownership to the native HACS integration, preserving the same entity IDs.
def strip_predictor_templates(path: str) -> None:
    p = Path(path)
    s = p.read_text(encoding="utf-8")
    marker = "      # 3.1.1 — Recorder-friendly AI Thermal Predictor sensors (observe-only).\n"
    start = s.find(marker)
    if start < 0:
        raise SystemExit(f"predictor template marker missing in {path}")
    # End immediately before the next template sensor following the four predictor sensors.
    conf = s.find("        unique_id: sbc5_ai_thermal_predictor_confidence", start)
    if conf < 0:
        raise SystemExit(f"predictor confidence missing in {path}")
    next_sensor = s.find("\n      - name:", conf + 1)
    if next_sensor < 0:
        raise SystemExit(f"next sensor after predictor missing in {path}")
    s = s[:start] + "      # AI Thermal Predictor entities are native integration sensors since 3.1.2.\n" + s[next_sensor+1:]
    p.write_text(s, encoding="utf-8")

for path in (
    "packages/sbc5_control_center.yaml",
    "local_apps/sbc5_control_center/migration_assets/sbc5_control_center.yaml",
    "local_apps/sbc5_control_center/migration_assets/rpi5_control_center.yaml",
):
    strip_predictor_templates(path)

# 5) Make Ingress status explicit about stale browser views after a successful save.
html = Path("local_apps/sbc5_control_center/config_ui/index.html")
s = html.read_text(encoding="utf-8")
s = s.replace(
    "Karta została zsynchronizowana do Card UI v'+vv+'. Odśwież dashboard Test.",
    "Karta została zsynchronizowana do Card UI v'+vv+'. Zamknij i otwórz ponownie dashboard, aby wyczyścić cache widoku.",
)
html.write_text(s, encoding="utf-8")

print("3.1.2 source fixes applied")
