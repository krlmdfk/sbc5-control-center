# SBC5 Control Center 3.2.1 — isolated offline Canary

**This is a separate, manually started diagnostic Home Assistant App.** It is **not**
the full SBC5 controller and must never be used as a replacement for fan cooling.

**To osobna aplikacja diagnostyczna uruchamiana ręcznie.** Nie zastępuje kontrolera
wentylatora, nie steruje GPIO/PWM i nie może przejmować chłodzenia.

## Safety guarantees / Bezpieczeństwo

- Different local App identity: \`sbc5_control_center_canary\`.
- \`boot: manual\`, \`full_access: false\`, no privileged/host PID access.
- No Home Assistant/Supervisor APIs or host configuration mounts.
- Only \`/share\` is mounted **read-only**.
- No update, migration, restore, AI training, calibration, or reset commands.
- No modifications to an existing App, dashboard, host, fan, or source model.
- The Canary does **not execute** any code from the inspected archive.

## Installation / Instalacja

1. Verify that the current SBC5 Control Center is working and make a Home Assistant
   backup before testing.
2. From the GitHub Actions Canary workflow artifact, extract the folder
   \`sbc5_control_center_canary\` under the Home Assistant **local apps/add-ons
   development directory** \`/addons/\`. The result is
   \`/addons/sbc5_control_center_canary/config.yaml\` with \`Dockerfile\`,
   \`canary_runner.py\`, and \`README.md\` alongside it.
3. In Home Assistant, open the Apps/Add-on Store, refresh the list, and look for
   **SBC5 Control Center Canary — Offline AI Shadow Test**. Install it but keep
   auto-start/watchdog off.
4. In the shared **/share** folder, create \`sbc5_canary\`. Place the separately
   verified \`SBC5_3.2.1_OFFLINE_INSPECTION_ONLY.zip\` from the offline CI artifact
   there. Do not confuse it with the Canary local-app folder ZIP.
5. Optional: place an **independent backup copy**, not the live model, at
   \`/share/sbc5_canary/ai_cooling_model.json\`. Do not publish this file; it may
   contain private training data.
6. Start the Canary **manually**. It checks the package manifest, version,
   expected runtime dependencies, and SHA-256 of every member. If a model copy
   is present, it reports schema, counters and hash without modifying the copy.
7. Open Canary logs. On success, \`archive.result\` is \`PASS\`; the one-shot
   process then exits. Do not enable automatic startup or watchdog.

## Ograniczenia

To **nie jest pełny test sterowania AI Cooling**. Sprawdza jedynie integralność
kandydata 3.2.1 oraz opcjonalnej kopii modelu, izolując je od rzeczywistego
sterowania wentylatorem. Nie sprawdza aktualizacji na działającym urządzeniu,
reakcji PWM na sprzęt ani przywracania kopii Home Assistant.

## Stop conditions / Kiedy przerwać

Stop if package verification is FAIL, the version differs, a ZIP member is
missing, the local App unexpectedly requests privileges, or the existing SBC5
controller behaves differently. Do not replace the stable App, install the
offline ZIP as an App update, or run any migration/AI reset for this test.
