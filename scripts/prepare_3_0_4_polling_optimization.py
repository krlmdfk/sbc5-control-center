#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
RUN = APP / "run_legacy.sh"
CONFIG = APP / "config.yaml"
CONFIG_UI = APP / "config_ui.py"
EN = APP / "translations" / "en.yaml"
PL = APP / "translations" / "pl.yaml"
CARGO = APP / "rust-core" / "Cargo.toml"
LOCK = APP / "rust-core" / "Cargo.lock"
VERSION = "3.0.4"

text = RUN.read_text(encoding="utf-8")
text = re.sub(r'(?m)^APP_VERSION="[^"]+"$', f'APP_VERSION="{VERSION}"', text, count=1)
text = re.sub(r'(?m)^REQUIRED_PACKAGE_VERSION="[^"]+"$', f'REQUIRED_PACKAGE_VERSION="{VERSION}"', text, count=1)
text = text.replace('AI_RUNTIME_RELAY_INTERVAL_SECONDS=15', 'AI_RUNTIME_RELAY_INTERVAL_SECONDS=30', 1)

anchor = 'CONFIG_DISABLED_POLL_SECONDS=30\n'
if anchor not in text:
    raise SystemExit('CONFIG_DISABLED_POLL_SECONDS anchor not found')
text = text.replace(anchor, anchor + 'CONFIG_TXT_WATCHDOG_MIN_SECONDS=30\n', 1)

old_local = 'config_txt_options_sync_loop() {\n  local sig interval enabled settings\n'
new_local = 'config_txt_options_sync_loop() {\n  local sig interval enabled settings effective_interval\n'
if old_local not in text:
    raise SystemExit('config_txt_options_sync_loop local anchor not found')
text = text.replace(old_local, new_local, 1)

old_interval = '''    num_in_range "${interval:-5}" 2 60 || interval=5

    if [ "$enabled" != "true" ]; then
      sleep "$CONFIG_DISABLED_POLL_SECONDS"
      continue
    fi

    sleep "$interval"
'''
new_interval = '''    num_in_range "${interval:-30}" 2 60 || interval=30
    effective_interval="$interval"
    if [ "$effective_interval" -lt "$CONFIG_TXT_WATCHDOG_MIN_SECONDS" ] 2>/dev/null; then
      effective_interval="$CONFIG_TXT_WATCHDOG_MIN_SECONDS"
    fi

    if [ "$enabled" != "true" ]; then
      sleep "$CONFIG_DISABLED_POLL_SECONDS"
      continue
    fi

    sleep "$effective_interval"
'''
if old_interval not in text:
    raise SystemExit('config.txt watchdog interval anchor not found')
text = text.replace(old_interval, new_interval, 1)

old_log = 'log "Config.txt Options UI: enabled=${CONFIG_TXT_OPTIONS_ENABLED}, sync=${CONFIG_TXT_OPTIONS_SYNC_INTERVAL}s, advanced=${CONFIG_TXT_OPTIONS_ADVANCED}"'
new_log = 'log "Config.txt Options UI: enabled=${CONFIG_TXT_OPTIONS_ENABLED}, configured_sync=${CONFIG_TXT_OPTIONS_SYNC_INTERVAL}s, watchdog_min=${CONFIG_TXT_WATCHDOG_MIN_SECONDS}s, event_reload=immediate, advanced=${CONFIG_TXT_OPTIONS_ADVANCED}"'
if old_log not in text:
    raise SystemExit('config.txt startup log anchor not found')
text = text.replace(old_log, new_log, 1)

old_perf = 'AI-log-keepalive=$((AI_COOLING_LOG_KEEPALIVE_CYCLES * ADAPTIVE_PWM_INTERVAL_SECONDS))s.'
new_perf = 'AI-log-keepalive=$((AI_COOLING_LOG_KEEPALIVE_CYCLES * ADAPTIVE_PWM_INTERVAL_SECONDS))s; config-watchdog>=${CONFIG_TXT_WATCHDOG_MIN_SECONDS}s.'
if old_perf not in text:
    raise SystemExit('performance log anchor not found')
text = text.replace(old_perf, new_perf, 1)
RUN.write_text(text, encoding="utf-8")

cfg = CONFIG.read_text(encoding="utf-8")
cfg = cfg.replace('sync_interval_seconds: 5', 'sync_interval_seconds: 30', 1)
CONFIG.write_text(cfg, encoding="utf-8")

ui = CONFIG_UI.read_text(encoding="utf-8")
ui = ui.replace("'config_txt_manager':{'enabled':False,'sync_interval_seconds':5,'advanced_mode':False}", "'config_txt_manager':{'enabled':False,'sync_interval_seconds':30,'advanced_mode':False}", 1)
CONFIG_UI.write_text(ui, encoding="utf-8")

en = EN.read_text(encoding="utf-8")
en = en.replace('description: 2–60 seconds; default 5.', 'description: 2–60 seconds configured; default 30. Runtime watchdog minimum is 30 seconds; UI saves still apply immediately.', 1)
EN.write_text(en, encoding="utf-8")

pl = PL.read_text(encoding="utf-8")
pl = pl.replace('description: Synchronizacja co 2–60 s; domyślnie 5 s. Zapis nie uruchamia SBC5 automatycznie.', 'description: Ustawienie 2–60 s; domyślnie 30 s. Minimalny watchdog runtime to 30 s, a zapis z UI nadal jest stosowany natychmiast.', 1)
PL.write_text(pl, encoding="utf-8")

cargo = CARGO.read_text(encoding="utf-8")
cargo, n = re.subn(r'(?m)^version = "[^"]+"$', f'version = "{VERSION}"', cargo, count=1)
if n != 1:
    raise SystemExit('Cargo.toml version anchor not found')
CARGO.write_text(cargo, encoding="utf-8")

lock = LOCK.read_text(encoding="utf-8")
lock, n = re.subn(r'(?ms)(name = "sbc5-core"\nversion = ")[^"]+(\")', rf'\g<1>{VERSION}\2', lock, count=1)
if n != 1:
    raise SystemExit('Cargo.lock sbc5-core version anchor not found')
LOCK.write_text(lock, encoding="utf-8")

print('Prepared SBC5 3.0.4 polling/I-O optimization anchors')
