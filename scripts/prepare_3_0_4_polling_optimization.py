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
text, n = re.subn(r'(?m)^APP_VERSION="[^"]+"$', f'APP_VERSION="{VERSION}"', text, count=1)
if n != 1: raise SystemExit('APP_VERSION anchor not found')
text, n = re.subn(r'(?m)^REQUIRED_PACKAGE_VERSION="[^"]+"$', f'REQUIRED_PACKAGE_VERSION="{VERSION}"', text, count=1)
if n != 1: raise SystemExit('REQUIRED_PACKAGE_VERSION anchor not found')
text, n = re.subn(r'(?m)^AI_RUNTIME_RELAY_INTERVAL_SECONDS=\d+$', 'AI_RUNTIME_RELAY_INTERVAL_SECONDS=30', text, count=1)
if n != 1: raise SystemExit('AI relay interval anchor not found')

anchor = 'CONFIG_DISABLED_POLL_SECONDS=30\n'
if anchor not in text:
    raise SystemExit('CONFIG_DISABLED_POLL_SECONDS anchor not found')
text = text.replace(anchor, anchor + 'CONFIG_TXT_WATCHDOG_MIN_SECONDS=30\n', 1)

pattern_local = r'(config_txt_options_sync_loop\(\)\s*\{\s*\n\s*local\s+)([^\n]+)'
m = re.search(pattern_local, text)
if not m:
    raise SystemExit('config_txt_options_sync_loop local anchor not found')
locals_line = m.group(2)
if 'effective_interval' not in locals_line:
    locals_line = locals_line.rstrip() + ' effective_interval'
text = text[:m.start(2)] + locals_line + text[m.end(2):]

pattern_interval = re.compile(
    r'(?ms)(\s*num_in_range\s+"\$\{interval:-5\}"\s+2\s+60\s+\|\|\s+interval=5\s*\n)'
    r'(\s*if\s+\[\s+"\$enabled"\s+!=\s+"true"\s+\];\s+then\s*\n\s*sleep\s+"\$CONFIG_DISABLED_POLL_SECONDS"\s*\n\s*continue\s*\n\s*fi\s*\n)'
    r'(\s*sleep\s+"\$interval"\s*\n)'
)
m = pattern_interval.search(text)
if not m:
    raise SystemExit('config.txt watchdog interval anchor not found')
replacement = '''    num_in_range "${interval:-30}" 2 60 || interval=30
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
text = text[:m.start()] + '\n' + replacement + text[m.end():]

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
cfg, n = re.subn(r'(?m)^(\s*sync_interval_seconds:\s*)5\s*$', r'\g<1>30', cfg, count=1)
if n != 1: raise SystemExit('config.yaml sync default anchor not found')
CONFIG.write_text(cfg, encoding="utf-8")

ui = CONFIG_UI.read_text(encoding="utf-8")
ui, n = re.subn(r"('config_txt_manager'\s*:\s*\{[^\n]*?'sync_interval_seconds'\s*:\s*)5", r'\g<1>30', ui, count=1)
if n != 1: raise SystemExit('config_ui.py sync default anchor not found')
CONFIG_UI.write_text(ui, encoding="utf-8")

en = EN.read_text(encoding="utf-8")
en, n = re.subn(r'description: 2–60 seconds; default 5\.', 'description: 2–60 seconds configured; default 30. Runtime watchdog minimum is 30 seconds; UI saves still apply immediately.', en, count=1)
if n != 1: raise SystemExit('English translation sync description anchor not found')
EN.write_text(en, encoding="utf-8")

pl = PL.read_text(encoding="utf-8")
pl, n = re.subn(r'description: Synchronizacja co 2–60 s; domyślnie 5 s\. Zapis nie uruchamia SBC5 automatycznie\.', 'description: Ustawienie 2–60 s; domyślnie 30 s. Minimalny watchdog runtime to 30 s, a zapis z UI nadal jest stosowany natychmiast.', pl, count=1)
if n != 1: raise SystemExit('Polish translation sync description anchor not found')
PL.write_text(pl, encoding="utf-8")

cargo = CARGO.read_text(encoding="utf-8")
cargo, n = re.subn(r'(?m)^version = "[^"]+"$', f'version = "{VERSION}"', cargo, count=1)
if n != 1: raise SystemExit('Cargo.toml version anchor not found')
CARGO.write_text(cargo, encoding="utf-8")

lock = LOCK.read_text(encoding="utf-8")
lock, n = re.subn(r'(?ms)(name = "sbc5-core"\nversion = ")[^"]+(\")', rf'\g<1>{VERSION}\2', lock, count=1)
if n != 1: raise SystemExit('Cargo.lock sbc5-core version anchor not found')
LOCK.write_text(lock, encoding="utf-8")

print('Prepared SBC5 3.0.4 polling/I-O optimization anchors')
