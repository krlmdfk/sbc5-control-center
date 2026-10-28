#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / "local_apps/sbc5_control_center/run_legacy.sh").read_text(encoding="utf-8")

required = [
    "package_version_on_disk()",
    "bridge_version_on_disk()",
    "restart_prompt_owned_by_hacs()",
    "HACS/Marketplace ma już bridge",
    "jest już zsynchronizowany na dysku",
    "fast-up +8pp @ +5°C; critical-up +12pp @ +7°C; fast-down -5pp",
]
for token in required:
    assert token in text, token

assert "Podmień packages/sbc5_control_center.yaml" not in text
assert '[ -f "$BRIDGE_EXTERNAL_MARKER" ] || return 1' in text
assert '[ "$(package_version_on_disk)" = "$REQUIRED_PACKAGE_VERSION" ] || return 1' in text
assert '[ "$(bridge_version_on_disk)" = "$APP_VERSION" ] || return 1' in text

# A HACS-owned/current bridge suppresses only the duplicate native Repair; the
# canonical RESTART_REQUIRED_TYPE remains home_assistant until Core reloads the
# package, so dashboard/health tracking is preserved.
assert 'RESTART_REQUIRED_TYPE="home_assistant"' in text
print("restart-manager HACS handoff hotfix: PASS")
