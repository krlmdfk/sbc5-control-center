# SBC5 Control Center — Local → Apps Store migration / Migracja Local → Apps Store

## English

SBC5 2.8.31 provides a one-time handoff from the historical local App identity to the App installed from the Home Assistant Apps store.

### Safety model

- The local and Store identities never share private `/data` directly.
- The local source exports only allow-listed durable SBC5 state to `/config/sbc5_control_center/migration/store_handoff_v1/`.
- Every exported file is protected by SHA-256 and a bundle fingerprint.
- The Store identity imports the bundle **before** profile/bootstrap/controller startup.
- A migration profile guard prevents stale Store/Supervisor `Factory/off` defaults from being treated as an explicit user edit until imported durable CPU/GPU state is written to native App options.
- Import is blocked while the local source App is still running.
- Before import, the Store identity creates a rollback backup in `/data/migration_backups/`.
- After a successful import the local identity enters safe standby if it is started again.

### Migrated state

The handoff includes the local AI model, AI grid profile, fan calibration, CPU/GPU profile state, custom-curve state, selected configuration/options and safety markers that represent intentional configuration choices. Runtime locks, update caches, restart markers and transient telemetry are regenerated instead of migrated.

### Cutover

1. Keep the Store App stopped.
2. Update the existing local SBC5 App to 2.8.31 with the verified local ZIP package.
3. After the local App starts, confirm the log contains `Store Migration` and `export_ready`.
4. Update the Store App to 2.8.31 in Home Assistant Apps, but keep it stopped until the local export is ready.
5. Stop the local App.
6. Start the Store App. It verifies and imports the handoff before starting the controller.
7. Verify AI observations/model, fan calibration, CPU/GPU requested profiles, temperature, RPM and PWM.
8. Only after verification, uninstall the historical local App. Do not remove the migration handoff until the Store instance is verified.

### Hybrid updates after migration

- **Store-managed full App runtime:** normal path is Home Assistant Apps.
- **Local ZIP, dashboard/UI-only:** remains directly supported.
- **Local ZIP, full runtime on a Store installation:** SBC5 verifies the local ZIP and delegates the actual App replacement to the native Home Assistant Apps update endpoint **only when the identical version is already published in the Store**. This preserves Supervisor ownership and update tracking.
- **Local installation:** full verified ZIP updates continue to rebuild the local App as before.
- **HACS integration:** remains independently managed by HACS.

Rollback command exposed through App stdin: `migration_rollback`. A restart of the Store App is required after rollback.

---

## Polski

SBC5 2.8.31 udostępnia jednorazowy, kontrolowany handoff ze starej lokalnej tożsamości aplikacji do aplikacji instalowanej ze sklepu Apps Home Assistant.

### Model bezpieczeństwa

- Lokalna i sklepowa instancja nie kopiują prywatnego `/data` bezpośrednio między kontenerami.
- Lokalna instancja eksportuje tylko jawnie dozwolony trwały stan SBC5 do `/config/sbc5_control_center/migration/store_handoff_v1/`.
- Każdy plik jest zabezpieczony SHA-256 oraz fingerprintem całej paczki.
- Instancja sklepowa importuje dane **przed** bootstrapem profili i startem regulatora.
- Guard profili migracyjnych blokuje potraktowanie starych domyślnych wartości Store/Supervisor `Factory/off` jako świadomej zmiany użytkownika, dopóki zaimportowany trwały stan CPU/GPU nie zostanie zapisany do natywnej Konfiguracji aplikacji.
- Import jest blokowany, dopóki lokalna instancja źródłowa nadal działa.
- Przed importem wersja sklepowa tworzy backup rollback w `/data/migration_backups/`.
- Po poprawnym imporcie stara lokalna instancja, jeśli zostanie ponownie uruchomiona, przechodzi w bezpieczny standby zamiast uruchamiać regulator.

### Migrowany stan

Handoff obejmuje model AI, profil siatki AI, kalibrację wentylatora, stan profili CPU/GPU, konfigurację krzywej własnej, opcje użytkownika i trwałe markery będące świadomymi wyborami konfiguracyjnymi. Locki runtime, cache aktualizacji, markery restartów i chwilowa telemetria są odtwarzane na nowo.

### Przejście na wersję sklepową

1. Pozostaw wersję sklepową zatrzymaną.
2. Zaktualizuj obecną lokalną aplikację SBC5 do 2.8.31 zweryfikowanym lokalnym ZIP-em.
3. Po starcie lokalnej aplikacji sprawdź w logu `Store Migration` oraz `export_ready`.
4. Zaktualizuj aplikację sklepową do 2.8.31 w Home Assistant Apps, ale pozostaw ją zatrzymaną do czasu gotowego eksportu.
5. Zatrzymaj lokalną aplikację.
6. Uruchom aplikację sklepową. Zweryfikuje i zaimportuje handoff przed uruchomieniem regulatora.
7. Sprawdź model/próbki AI, kalibrację wentylatora, żądane profile CPU/GPU, temperaturę, RPM i PWM.
8. Dopiero po weryfikacji odinstaluj starą lokalną aplikację. Nie usuwaj handoffu przed potwierdzeniem poprawnej pracy wersji sklepowej.

### Aktualizacje hybrydowe po migracji

- **Pełny runtime wersji sklepowej:** podstawowy kanał to Home Assistant Apps.
- **Lokalny ZIP tylko dashboard/UI:** nadal działa bezpośrednio.
- **Pełny lokalny ZIP na instalacji sklepowej:** SBC5 weryfikuje ZIP i deleguje właściwą podmianę aplikacji do natywnego mechanizmu Apps **tylko gdy identyczna wersja jest już opublikowana w sklepie**. Dzięki temu Supervisor nadal prawidłowo śledzi wersję i aktualizacje.
- **Instalacja lokalna:** pełne, zweryfikowane ZIP-y nadal przebudowują lokalną aplikację jak dotychczas.
- **Integracja HACS:** pozostaje niezależnie zarządzana przez HACS.

Polecenie rollback dostępne przez stdin aplikacji: `migration_rollback`. Po rollbacku wymagany jest restart aplikacji sklepowej.
