#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "local_apps" / "sbc5_control_center" / "run_legacy.sh"
VALIDATE = ROOT / ".github" / "workflows" / "validate.yml"
TEST = ROOT / "scripts" / "test_restart_manager_hacs_handoff.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, got {count}")
    return text.replace(old, new, 1)


def main() -> int:
    text = RUN.read_text(encoding="utf-8")

    helper_marker = "\npublish_restart_requirement() {\n"
    helper = r'''

package_version_on_disk() {
  sed -n 's/^# SBC5 Control Center Package Version:[[:space:]]*//p' \
    /homeassistant/packages/sbc5_control_center.yaml 2>/dev/null | head -n1
}

bridge_version_on_disk() {
  jq -r '.version // empty' "$BRIDGE_DEST_DIR/manifest.json" 2>/dev/null || true
}

restart_prompt_owned_by_hacs() {
  # 3.1.9: when HACS already owns and has installed the current bridge, HACS
  # presents its own native restart repair. SBC5 keeps its internal restart state
  # for dashboard/health tracking, but must not create a second duplicate Repair.
  [ "$RESTART_REQUIRED_TYPE" = "home_assistant" ] || return 1
  [ -f "$BRIDGE_EXTERNAL_MARKER" ] || return 1
  [ "$(package_version_on_disk)" = "$REQUIRED_PACKAGE_VERSION" ] || return 1
  [ "$(bridge_version_on_disk)" = "$APP_VERSION" ] || return 1
  return 0
}
'''
    if "restart_prompt_owned_by_hacs()" not in text:
        text = replace_once(text, helper_marker, helper + helper_marker, "insert HACS restart ownership helpers")

    old_mismatch = r'''  if [ "$LOADED_PACKAGE_VERSION" != "$REQUIRED_PACKAGE_VERSION" ]; then
    RESTART_REQUIRED_TYPE="home_assistant"
    RESTART_REQUIRED_REASON="Pakiet Home Assistant nie jest jeszcze wczytany w wersji ${REQUIRED_PACKAGE_VERSION} (aktualnie: ${LOADED_PACKAGE_VERSION}). Podmień packages/sbc5_control_center.yaml z tej wersji aplikacji, a następnie uruchom ponownie Home Assistant."
  fi
}'''
    new_mismatch = r'''  if [ "$LOADED_PACKAGE_VERSION" != "$REQUIRED_PACKAGE_VERSION" ]; then
    local disk_package_version=""
    disk_package_version="$(package_version_on_disk)"
    RESTART_REQUIRED_TYPE="home_assistant"
    if [ "$disk_package_version" = "$REQUIRED_PACKAGE_VERSION" ]; then
      RESTART_REQUIRED_REASON="Pakiet Home Assistant ${REQUIRED_PACKAGE_VERSION} jest już zsynchronizowany na dysku; bieżący Core ma nadal aktywną wersję ${LOADED_PACKAGE_VERSION}. Wymagany jest wyłącznie restart Home Assistant, aby wczytać nowy package."
    else
      RESTART_REQUIRED_REASON="Pakiet Home Assistant na dysku nie jest zgodny z wymaganą wersją ${REQUIRED_PACKAGE_VERSION} (plik: ${disk_package_version:-brak}, aktywnie w Core: ${LOADED_PACKAGE_VERSION}). Uruchom ponownie synchronizację/aktualizację SBC5 przed restartem Home Assistant."
    fi
  fi
}'''
    text = replace_once(text, old_mismatch, new_mismatch, "replace package mismatch message")

    old_publish = r'''    native_restart_repair_set "$RESTART_REQUIRED_TYPE" "$RESTART_REQUIRED_REASON" "$post_from" "$post_to"
    if [ "$force_notify" = "true" ] || [ "$RESTART_REQUIRED_TYPE" != "$LAST_RESTART_STATE" ]; then
      ha_restart_notification "$RESTART_REQUIRED_TYPE" "$RESTART_REQUIRED_REASON"
    fi'''
    new_publish = r'''    if restart_prompt_owned_by_hacs; then
      if [ -r "$NATIVE_RESTART_MARKER" ] || [ -r "$NATIVE_REPAIR_POSTED_FILE" ]; then
        native_restart_repair_clear || true
      fi
      ha_dismiss_restart_notification
      if [ "$force_notify" = "true" ] || [ "$RESTART_REQUIRED_TYPE" != "$LAST_RESTART_STATE" ]; then
        log "Restart Manager: HACS/Marketplace ma już bridge ${APP_VERSION} i package ${REQUIRED_PACKAGE_VERSION} na dysku — nie tworzę drugiego Repair; oczekuję tylko na restart Home Assistant."
      fi
    else
      native_restart_repair_set "$RESTART_REQUIRED_TYPE" "$RESTART_REQUIRED_REASON" "$post_from" "$post_to"
      if [ "$force_notify" = "true" ] || [ "$RESTART_REQUIRED_TYPE" != "$LAST_RESTART_STATE" ]; then
        ha_restart_notification "$RESTART_REQUIRED_TYPE" "$RESTART_REQUIRED_REASON"
      fi
    fi'''
    text = replace_once(text, old_publish, new_publish, "deduplicate HACS/SBC5 restart repairs")

    old_slew = "actuator slew=+3/-4pp na cykl (fast +5/-5)"
    new_slew = "actuator slew=+3/-4pp na cykl (fast-up +8pp @ +5°C; critical-up +12pp @ +7°C; fast-down -5pp)"
    text = replace_once(text, old_slew, new_slew, "refresh thermal fast-path startup description")

    RUN.write_text(text, encoding="utf-8")

    TEST.write_text(
        '''#!/usr/bin/env python3\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\ntext = (ROOT / "local_apps/sbc5_control_center/run_legacy.sh").read_text(encoding="utf-8")\n\nrequired = [\n    "package_version_on_disk()",\n    "bridge_version_on_disk()",\n    "restart_prompt_owned_by_hacs()",\n    "HACS/Marketplace ma już bridge",\n    "jest już zsynchronizowany na dysku",\n    "fast-up +8pp @ +5°C; critical-up +12pp @ +7°C; fast-down -5pp",\n]\nfor token in required:\n    assert token in text, token\n\nassert "Podmień packages/sbc5_control_center.yaml" not in text\nassert '[ -f "$BRIDGE_EXTERNAL_MARKER" ] || return 1' in text\nassert '[ "$(package_version_on_disk)" = "$REQUIRED_PACKAGE_VERSION" ] || return 1' in text\nassert '[ "$(bridge_version_on_disk)" = "$APP_VERSION" ] || return 1' in text\n\n# A HACS-owned/current bridge suppresses only the duplicate native Repair; the\n# canonical RESTART_REQUIRED_TYPE remains home_assistant until Core reloads the\n# package, so dashboard/health tracking is preserved.\nassert 'RESTART_REQUIRED_TYPE="home_assistant"' in text\nprint("restart-manager HACS handoff hotfix: PASS")\n''',
        encoding="utf-8",
    )

    workflow = VALIDATE.read_text(encoding="utf-8")
    needle = "      - name: Check whitespace errors\n        run: git diff --check HEAD^ HEAD || git diff --check\n"
    step = "      - name: Test Restart Manager HACS handoff\n        run: python scripts/test_restart_manager_hacs_handoff.py\n\n"
    if step not in workflow:
        workflow = replace_once(workflow, needle, step + needle, "add restart-manager regression test")
        VALIDATE.write_text(workflow, encoding="utf-8")

    print("Prepared restart-manager/HACS handoff hotfix source changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
