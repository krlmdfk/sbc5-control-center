# SBC5 Control Center 3.2.1 — offline candidate verification / weryfikacja kandydata

> **NOT AN INSTALLATION INSTRUCTION / NIE JEST TO INSTRUKCJA INSTALACJI.**
> This branch builds a CI-only **offline inspection** archive, not a GitHub Release or HACS update.
> Ta gałąź buduje archiwum **wyłącznie do kontroli w CI**, nie publikuje aktualizacji ani integracji HACS.

## Purpose / Cel

- Reconstruct version 3.2.1 metadata **only in an ephemeral GitHub Actions workspace**.
- Rebuild the manifest, ensuring all Dockerfile \`COPY\` inputs are included.
- Run strict manifest checks, ZIP SHA-256 verification and ZIP security preflight.
- Include read-only AI diagnostics and synthetic upgrade/restart/concurrency regressions.
- Preserve public 3.2.0 release and keep all PRs in Draft until reviewed.

## Hard stops / Warunki blokujące wdrożenie

Do **not** install the CI archive on a running Raspberry Pi 5. In particular, **do not copy it**
to \`/config/sbc5_control_center_updates/\` and do not activate it using any SBC5 update command.
It has not been tested with the actual \`3.2.1-rc2\` build or the user's persisted AI model.

**Nie instaluj archiwum CI na działającym Raspberry Pi 5.** Nie kopiuj go do katalogu
aktualizacji i nie uruchamiaj aktualizacji na jego podstawie.

Before a subsequent separately approved hardware test, all of these conditions must be met:

1. Obtain the actual installed-version, App/Store slug and Home Assistant / App backup state.
2. Make a full Home Assistant backup with the App's persistent data and confirm its restore path.
3. Make and verify an independent copy of \`/data/ai_cooling_model.json\` from **inside the SBC5 App container**.
4. Collect only non-sensitive diagnostic counts (model schema, observations, qualified samples, SHA-256, backup discovery).
5. Review the exact 3.2.1 candidate commit and archive hash; confirm HACS integration version coordination.
6. Test in a non-production canary or controlled maintenance window, with fan safety operating independently of AI.
7. Re-check AI counters, CPU/GPU configuration, fan profile, Card UI sync and controller ownership after restart.
8. Confirm a rollback path **before** the first installation; never run \`reset\` or migration rollback as a diagnostic experiment.

## Safe model-copy example / Przykład bezpiecznej kopii modelu

These commands must be run **inside the SBC5 App's container**, not an ordinary HA Terminal
that lacks access to its private \`/data\`. They create a backup and validate it; they
do not alter or reset the active model.

Poniższe polecenia dotyczą **kontenera aplikacji SBC5**, nie ogólnego terminala HAOS.

\`\`\`sh
set -eu
umask 077
model=/data/ai_cooling_model.json
test -s "$model" || { echo "BRAK MODELU — przerwij test"; exit 1; }
install -d -m 700 /data/ai_model_backups
backup="/data/ai_model_backups/pre_3_2_1_$(date +%Y%m%d_%H%M%S).json"
cp -p -- "$model" "$backup"
test -s "$backup"
python3 -m json.tool "$backup" >/dev/null
sha256sum "$backup"
echo "Backup verified: $backup"
\`\`\`

If the file is missing, corrupt, or counters unexpectedly fall, stop the test and
inspect backups. A SHA-256 difference between a copy and the **later live model** can
be normal while the model continues learning, because the model is rewritten atomically.

Jeżeli model nie istnieje, jest uszkodzony lub liczniki nieoczekiwanie spadają,
przerwij test i sprawdź kopie. Aktualnie uczący się model może mieć później inny hash.

## Post-update read-only inventory / Odczyt diagnostyczny po aktualizacji

Only after a verified candidate is installed in an authorized test environment, its
packaged script can be used to report metadata without modifying the learned state:

\`\`\`sh
python3 /ai_model_diagnostics.py --limit 12
\`\`\`

Do not upload complete learned JSON, configuration secrets or HA backups to public
GitHub issues or pull-request logs.

## Release coordination

- App and HACS integration **3.2.0** remain the public releases.
- HACS PR #36 is the draft migration parity candidate.
- App PR #66 contains the full current integrated safety fixes; this branch adds
  only CI-only preparation, the testing workflow and this runbook.
- Do not change production release versions, tags or HACS without a separate, reviewed release.
