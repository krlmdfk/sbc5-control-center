#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
RUN = APP / "run_legacy.sh"
CARGO = APP / "rust-core" / "Cargo.toml"
RELEASE_PREPARE = ROOT / "scripts" / "release_prepare.py"
VERSION = "3.0.2"

text = RUN.read_text(encoding="utf-8")

# Runtime version parity (release_prepare intentionally does not rewrite run_legacy.sh).
text = re.sub(r'(?m)^APP_VERSION="[^"]+"$', f'APP_VERSION="{VERSION}"', text, count=1)
text = re.sub(r'(?m)^REQUIRED_PACKAGE_VERSION="[^"]+"$', f'REQUIRED_PACKAGE_VERSION="{VERSION}"', text, count=1)

# Fix false native-Supervisor change detection. profile_options_subset_from_json emits a newline
# when used directly in a pipeline, while supervisor_profile_marker_write hashes the command-
# substitution value with that trailing newline stripped. Canonicalize both through a local
# variable so the exact same bytes are hashed on both sides.
old_sig = '''supervisor_profile_signature_json() {
  profile_options_subset_from_json | sha256sum | awk '{print $1}'
}
'''
new_sig = '''supervisor_profile_signature_json() {
  local subset
  subset="$(profile_options_subset_from_json)" || return 1
  printf '%s' "$subset" | sha256sum | awk '{print $1}'
}
'''
if old_sig not in text:
    raise SystemExit("supervisor_profile_signature_json anchor not found")
text = text.replace(old_sig, new_sig, 1)

# Replace periodic full ZIP parsing with a cheap metadata signature. The normal full update
# check already runs 20 s after startup, so the local watcher only needs to react to changes
# that occur after startup. This keeps local update discovery responsive without reopening
# unchanged ZIP archives every two minutes.
old_watch = '''local_update_watch_loop() {
  sleep 45
  while true; do
    load_options
    if [ "$LOCAL_PACKAGE_UPDATES_ENABLED" = "true" ]; then
      check_app_update local_only || true
    fi
    sleep "$((LOCAL_PACKAGE_SCAN_INTERVAL_MINUTES * 60))"
  done
}
'''
new_watch = '''local_update_directory_signature() {
  local dir f
  {
    for dir in "$LOCAL_UPDATE_DIR" "$LEGACY_LOCAL_UPDATE_DIR" "$LEGACY_OLD_LOCAL_UPDATE_DIR"; do
      [ -d "$dir" ] || continue
      for f in "$dir"/*.zip; do
        [ -f "$f" ] || continue
        stat -c '%n|%s|%Y' "$f" 2>/dev/null || printf '%s|unknown\\n' "$f"
      done
    done
  } | sort | sha256sum | awk '{print $1}'
}

local_update_watch_loop() {
  local last_sig current_sig
  last_sig="$(local_update_directory_signature)"
  sleep 45
  while true; do
    load_options
    current_sig="$(local_update_directory_signature)"
    if [ "$LOCAL_PACKAGE_UPDATES_ENABLED" = "true" ]; then
      if [ "$current_sig" != "$last_sig" ]; then
        last_sig="$current_sig"
        check_app_update local_only || true
      fi
    else
      last_sig="$current_sig"
    fi
    sleep "$((LOCAL_PACKAGE_SCAN_INTERVAL_MINUTES * 60))"
  done
}
'''
if old_watch not in text:
    raise SystemExit("local_update_watch_loop anchor not found")
text = text.replace(old_watch, new_watch, 1)

RUN.write_text(text, encoding="utf-8")

cargo = CARGO.read_text(encoding="utf-8")
cargo, n = re.subn(r'(?m)^version = "[^"]+"$', f'version = "{VERSION}"', cargo, count=1)
if n != 1:
    raise SystemExit("Cargo package version anchor not found")
CARGO.write_text(cargo, encoding="utf-8")

# Permanently fix the release generator: config.yaml descriptions can be quoted/folded across
# multiple lines. Replace the whole YAML scalar block, not only the first physical line.
rp = RELEASE_PREPARE.read_text(encoding="utf-8")
old = '''    text = re.sub(r"(?m)^description:\\s*.*$", f"description: {json.dumps(desc, ensure_ascii=False)}", text, count=1)'''
new = '''    text = re.sub(
        r"(?ms)^description:\\s*.*?(?=^[A-Za-z_][A-Za-z0-9_-]*:\\s|\\Z)",
        f"description: {json.dumps(desc, ensure_ascii=False)}\\n",
        text,
        count=1,
    )'''
if old not in rp:
    raise SystemExit("release_prepare multiline description anchor not found")
rp = rp.replace(old, new, 1)
RELEASE_PREPARE.write_text(rp, encoding="utf-8")

print("Prepared SBC5 3.0.2 runtime optimization anchors")
