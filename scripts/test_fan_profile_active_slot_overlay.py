#!/usr/bin/env python3
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

# 3.1.18: userspace-managed custom1 on an active 1% grid is already effective.
# runtime=custom is the kernel's generic label and must not create a fake reboot request.
assert 'activation_state="active_runtime_managed"; activation_reason="adaptive_runtime_grid_active"' in run
assert '[ "$requested_code" = "custom1" ] && [ "$code" = "custom" ] && [ "$max_state" = "100" ]' in run
print("Fan profile active-slot overlay validation: PASS")
