#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "local_apps" / "sbc5_control_center" / "run_legacy.sh"
TEST = ROOT / "scripts" / "test_fan_profile_active_slot_overlay.py"

NEW_BLOCK = r'''fan_profile_active_boot_slot() {
  local slot="" cmdline=""
  # The running kernel is authoritative. HAOS/RPi5 exposes the RAUC slot in
  # the kernel command line; /proc is shared with the host kernel even when
  # SBC5 runs in the app container.
  cmdline="$(cat /proc/cmdline 2>/dev/null || true)"
  slot="$(printf '%s\n' "$cmdline" | sed -n 's/.*[[:space:]]rauc\.slot=\([AB]\)\([[:space:]].*\)\?$/\1/p')"
  if [ "$slot" = "A" ] || [ "$slot" = "B" ]; then
    printf '%s\n' "$slot"
    return 0
  fi

  # Fallback for diagnostics/older HAOS layouts: use the committed os_prefix.
  if [ -n "${BOOT_CFG:-}" ] && [ -r "$BOOT_CFG" ]; then
    slot="$(sed -n 's/^[[:space:]]*os_prefix=slot-\([AB]\)\/[[:space:]]*$/\1/p' "$BOOT_CFG" | tail -n1)"
  fi
  if [ "$slot" = "A" ] || [ "$slot" = "B" ]; then
    printf '%s\n' "$slot"
    return 0
  fi
  return 1
}

fan_profile_custom1_boot_artifacts_state() {
  local config_ok=false overlay_ok=false d active_slot="" active_overlay=""
  if ! find_boot_config; then
    printf 'false\tfalse\n'
    return 1
  fi

  if grep -Eq '^[[:space:]]*dtoverlay=rpi5-custom1([[:space:]]|$)' "$BOOT_CFG" 2>/dev/null \
     && grep -Eq '^[[:space:]]*dtparam=cooling_fan=on([[:space:]]|$)' "$BOOT_CFG" 2>/dev/null; then
    config_ok=true
  fi

  active_slot="$(fan_profile_active_boot_slot 2>/dev/null || true)"
  if [ "$active_slot" = "A" ] || [ "$active_slot" = "B" ]; then
    active_overlay="$BOOT_MP/slot-${active_slot}/overlays/rpi5-custom1.dtbo"
    [ -s "$active_overlay" ] && overlay_ok=true
    log "Fan Profile Boot Slot: active=${active_slot}; overlay=${active_overlay#$BOOT_MP/}; present=${overlay_ok}."
  else
    # Legacy/non-RAUC fallback only. Do not accept an arbitrary inactive slot
    # as proof that the currently booted firmware can load the overlay.
    d="$BOOT_MP/overlays/rpi5-custom1.dtbo"
    [ -s "$d" ] && overlay_ok=true
    log "Fan Profile Boot Slot: nie udało się ustalić aktywnego slotu RAUC; fallback=overlays/rpi5-custom1.dtbo; present=${overlay_ok}."
  fi

  printf '%s\t%s\n' "$config_ok" "$overlay_ok"
  cleanup_mount
  [ "$config_ok" = "true" ] && [ "$overlay_ok" = "true" ]
}

'''


def main() -> int:
    text = RUN.read_text(encoding="utf-8")
    pattern = re.compile(
        r"fan_profile_custom1_boot_artifacts_state\(\) \{.*?\n\}\n\nfan_profile_reconcile_startup\(\) \{",
        re.S,
    )
    match = pattern.search(text)
    if not match:
        raise SystemExit("fan_profile_custom1_boot_artifacts_state block not found")
    replacement = NEW_BLOCK + "fan_profile_reconcile_startup() {"
    text = text[: match.start()] + replacement + text[match.end() :]
    RUN.write_text(text, encoding="utf-8")

    TEST.write_text(r'''#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
run = (ROOT / "local_apps/sbc5_control_center/run_legacy.sh").read_text(encoding="utf-8")

assert "fan_profile_active_boot_slot()" in run
assert "rauc\\.slot=" in run
assert 'active_overlay="$BOOT_MP/slot-${active_slot}/overlays/rpi5-custom1.dtbo"' in run

# The regression: presence in any inactive slot must no longer satisfy overlay_ok.
block = re.search(
    r"fan_profile_custom1_boot_artifacts_state\(\) \{(.*?)\n\}\n\nfan_profile_reconcile_startup",
    run,
    re.S,
)
assert block, "artifact-state function missing"
body = block.group(1)
assert 'for d in "$BOOT_MP/overlays" "$BOOT_MP/slot-A/overlays" "$BOOT_MP/slot-B/overlays"' not in body
assert 'slot-${active_slot}/overlays/rpi5-custom1.dtbo' in body
assert 'fallback=overlays/rpi5-custom1.dtbo' in body

# copy_active_overlay_to_possible_locations intentionally still mirrors the DTBO
# to both A/B slots. The fix is validation of the active slot, not removal of the
# defensive mirror.
assert '"$BOOT_MP/slot-A/overlays"' in run
assert '"$BOOT_MP/slot-B/overlays"' in run
print("Fan profile active-slot overlay validation: PASS")
''', encoding="utf-8")
    print("Prepared active-slot overlay validation fix")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
