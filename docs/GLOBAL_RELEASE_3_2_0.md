# SBC5 Control Center 3.2.0 — Global Community Edition / Edycja globalna

> Status: **release candidate, not published** until all release gates pass. "Global" means a public, internationally usable **community App repository** plus the existing HACS integration. It does **not** mean the App has been accepted into the official Home Assistant Apps repository.

## English — international distribution

**Who it is for:** Home Assistant OS users with Raspberry Pi 5 (`raspberrypi5-64`, aarch64), HA OS 18.3 or later and Core 2026.10.1 or later.

**Installation channels**
1. Add `https://github.com/krlmdfk/sbc5-control-center` under **Settings → Apps → Install app → Repositories**. The public app repository works internationally; it is not in the official built-in App list.
2. Install and start **SBC5 Control Center App/runtime** on Raspberry Pi 5.
3. In HACS / Marketplace, search for **SBC5 Control Center** and install the companion **integration**. If discovery fails, use `https://github.com/krlmdfk/sbc5-control-center-integration` as a custom HACS Integration repository.
4. Restart Home Assistant when the integration requires it. The native entities do not replace the App runtime.
5. Optional full Lovelace dashboard: Mushroom, card-mod, ApexCharts Card.

**Security disclosure — read before installation:** this App requests `full_access: true`, `host_pid: true`, `apparmor: false`, `SYS_ADMIN`, `SYS_PTRACE`, Supervisor `manager` role and writable configuration mounts. Home Assistant assigns a **security score of 1** whenever `full_access: true` is set. **Protection Mode must be disabled** for host access. This grants extensive access to the Home Assistant host. Only install from a trusted source, maintain a verified backup, and restrict use to administrators. No claim of least privilege or independent penetration testing is made.

**Release gates (block publication unless all required evidence is recorded):**
- [ ] App repository validation, syntax/runtime tests and Rust CI pass on the release commit
- [ ] HACS, Hassfest, integration migration and repairs tests pass on 3.2.0
- [ ] App + HACS 3.2.0 manifests and published versions are identical
- [ ] Strict update-manifest SHA-256 verification and local ZIP build pass
- [ ] Clean install on a second Raspberry Pi 5 with documented OS/Core requirements
- [ ] Verify cooling fan safety on boot, under normal idle/load and when host access is denied
- [ ] Verify host platform guard blocks unsupported boards
- [ ] Verify CPU/GPU presets default to factory; AI defaults to Learning when enabled
- [ ] Test upgrade from 3.1.37, Home Assistant restart, state/AI/calibration persistence
- [ ] Test rollback to previous App/integration versions from a verified backup
- [ ] Confirm an actual HACS/Marketplace update reaches completion (not stuck at a progress percentage)
- [ ] Human review of privilege justification, code changes and user-facing warning

**Official Home Assistant catalog:** not automatic. Review official contribution policy and obtain maintainers' approval separately. Do not submit to the official repository until the security posture and physical testing have been reviewed.

Official references:
- https://contributors.home-assistant.io/apps/reference/configuration/
- https://contributors.home-assistant.io/apps/guides/security/
- https://www.home-assistant.io/common-tasks/os/

## Polski — dystrybucja globalna

**Zakres:** publiczna dystrybucja społecznościowa aplikacji dla Raspberry Pi 5 z Home Assistant OS (min. 18.3) i Home Assistant Core (min. 2026.10.1). Nie oznacza to automatycznej obecności aplikacji w oficjalnym katalogu Home Assistant.

**Instalacja:** dodaj główne repozytorium do sklepu **Apps**, zainstaluj aplikację, następnie zainstaluj oddzielną integrację SBC5 przez HACS/Marketplace. Dodatkowe karty Lovelace są opcjonalne.

**Ostrzeżenie bezpieczeństwa:** aplikacja wymaga wyłączonego Protection Mode oraz szerokich uprawnień do hosta. Home Assistant ocenia `full_access: true` na poziomie bezpieczeństwa **1**. Przed instalacją wykonaj kopię zapasową, sprawdź źródło i udziel dostępu tylko administratorom. To nie jest wersja po niezależnym audycie penetracyjnym.

**Warunki wydania:** zielone testy App/HACS, zgodność 3.2.0 i sum kontrolnych, czysta instalacja na drugim Raspberry Pi 5, test pracy wentylatora i zabezpieczeń, aktualizacja 3.1.37 → 3.2.0, weryfikacja zachowania stanu AI/kalibracji, test przywrócenia kopii oraz poprawne zakończenie aktualizacji integracji. Weryfikacje wymagające sprzętu muszą być wykonane na prawdziwym urządzeniu przed publikacją jako stabilnej wersji.

**Katalog oficjalny:** osobny proces przeglądu i akceptacji przez opiekunów Home Assistant; dostępność globalna przez własne repozytorium nie oznacza oficjalnej akceptacji.
