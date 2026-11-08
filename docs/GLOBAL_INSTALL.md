# Install SBC5 worldwide / Instalacja SBC5 na świecie

## English — Raspberry Pi 5, Home Assistant OS

SBC5 is globally accessible as a **community App repository**. Its companion integration is accepted in the HACS default catalog. The App itself is **not** an official Home Assistant App.

**Requirements:** Raspberry Pi 5 machine `raspberrypi5-64`, Home Assistant OS >= 18.3, Home Assistant Core >= 2026.10.1, administrator access and a verified system backup.

1. Go to **Settings → Apps → Install app → ⋮ → Repositories**. Add `https://github.com/krlmdfk/sbc5-control-center`.
2. Install **SBC5 Control Center** and read the host-access warning on the App page. It requests high system privileges and requires **Protection Mode off** to use the advertised host functions. Only proceed if you trust the code and accept this security tradeoff.
3. Start the App and confirm `Platform Guard: OK`, host-access telemetry and healthy fan readings. Keep factory CPU/GPU defaults; calibrate the fan before modifying cooling parameters.
4. Open **HACS / Marketplace**, search for **SBC5 Control Center**, and install the integration. Only if it does not appear, add `https://github.com/krlmdfk/sbc5-control-center-integration` as a custom Integration repository.
5. Restart Home Assistant when requested, then check **Settings → Devices & services** for SBC5.
6. Optionally install Mushroom, card-mod and ApexCharts Card for the full dashboard.

**If the integration update pauses:** avoid deleting the existing integration or its entity registry, allow one update at a time, and check Home Assistant Marketplace/HACS diagnostics before taking action. Save the installed `manifest.json` version and the error details.

**Security:** SBC5 currently uses `full_access` with a Home Assistant security score of 1. This is an intentional host-management tradeoff awaiting further least-privilege work. See [permission audit](SECURITY_PRIVILEGE_AUDIT_3_2_0.md).

**Validation note:** SBC5 3.2.0 is verified using automated clean-environment checks and an in-place upgrade on the existing Raspberry Pi 5. A clean install on a second physical Raspberry Pi 5 is not tested. CI cannot reproduce hardware fan, host access or boot conditions.

**Support:** https://github.com/krlmdfk/sbc5-control-center/issues

## Polski — Raspberry Pi 5, Home Assistant OS

SBC5 jest dostępne na całym świecie przez **publiczne repozytorium społecznościowe Apps**. Integracja jest przyjęta do katalogu HACS, ale sama aplikacja **nie znajduje się automatycznie w oficjalnym katalogu Home Assistant**.

**Wymagania:** Raspberry Pi 5, Home Assistant OS co najmniej 18.3, Core co najmniej 2026.10.1, dostęp administratora i sprawdzona kopia zapasowa.

1. **Ustawienia → Apps → Zainstaluj aplikację → ⋮ → Repozytoria:** dodaj `https://github.com/krlmdfk/sbc5-control-center`.
2. Zainstaluj SBC5 i zapoznaj się z informacją o uprawnieniach. Funkcje hosta wymagają wyłączenia **Protection Mode**, co zmniejsza izolację.
3. Uruchom aplikację, sprawdź `Platform Guard: OK`, odczyty wentylatora i temperatury. Na początek zachowaj fabryczne ustawienia CPU/GPU.
4. W HACS/Marketplace wyszukaj integrację **SBC5 Control Center**. Jeśli nie jest widoczna, dodaj repozytorium `https://github.com/krlmdfk/sbc5-control-center-integration` jako integrację niestandardową.
5. Po instalacji, jeśli pojawi się prośba, uruchom ponownie Home Assistant i sprawdź encje w **Ustawienia → Urządzenia i usługi**.
6. Opcjonalnie do pełnego dashboardu zainstaluj Mushroom, card-mod i ApexCharts Card.

**Zakres testów:** Weryfikujemy kod w czystym środowisku CI oraz aktualizację na istniejącym Raspberry Pi 5. Czysta instalacja na drugim fizycznym Raspberry Pi 5 nie została przetestowana. Testy CI nie symulują w pełni wentylatora i dostępu do hosta.

**Bezpieczeństwo:** `full_access` daje aplikacji ocenę bezpieczeństwa 1 w Home Assistant. Pełny audyt: [SECURITY_PRIVILEGE_AUDIT_3_2_0.md](SECURITY_PRIVILEGE_AUDIT_3_2_0.md).
