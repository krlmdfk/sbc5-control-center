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
- [ ] Clean-environment CI smoke tests for App packaging, integration manifests, dependency imports, platform guard and installer/update asset integrity (not a substitute for a real first installation)
- [ ] Verify cooling fan operation on the **existing** Raspberry Pi 5 with read-only telemetry at idle and normal load, before and after the upgrade; do not forcibly disable working cooling or host access
- [ ] Verify unsupported-machine rejection through automated platform-guard tests; the `raspberrypi5-64` install constraint is checked statically
- [ ] Verify CPU/GPU factory defaults and AI's opt-in learning mode via CI plus current-device settings review
- [ ] Test **in-place** upgrade from 3.1.37 on the existing Pi 5, after a verified backup, followed by restart and checks of state/AI/calibration persistence
- [ ] Validate backup and rollback **procedure** without disrupting live fan control; perform a real rollback only if safe/necessary
- [ ] Confirm an actual HACS/Marketplace update reaches completion (not stuck at a progress percentage)
- [ ] Document as an explicit release limitation: fresh physical installation on an independent Raspberry Pi 5 **not tested**; request independent community verification after publication
- [ ] Human review of privilege justification, code changes and user-facing warning

**Store-managed update limitation:** A full SBC5 ZIP on a Store-managed App cannot install an unpublished runtime version. It only delegates to the Supervisor update if the ZIP version exactly matches the version currently offered in the Apps store. Therefore, a 3.2.0 release-candidate ZIP is for **offline integrity / packaging inspection only**, never for insertion in `/config/sbc5_control_center_updates/` on the existing Store-managed installation. The in-place hardware upgrade can only be tested through the actual Apps update channel once 3.2.0 is exposed there. Before that, record a full backup and a read-only 3.1.37 health baseline. This is a release tradeoff: CI, package verification and review before publishing; supervised real-hardware upgrade observation after the version is made available. Do not claim pre-publication on-device verification if it was not performed.

**Single-device validation policy:** A second Raspberry Pi 5 is **optional** and not a publication blocker for the public community edition. CI's clean checkout/build cannot validate physical first-run behavior. Release notes must explicitly say "fresh installation on a second device not tested", and the only available Pi must not be reset, uninstalled, or used for destructive failure injection. A stable community release still requires successful in-place upgrade and normal fan-safety observations on the existing device. Acceptance into the official Home Assistant catalog remains separate.

**Official Home Assistant catalog:** not automatic. Review official contribution policy and obtain maintainers' approval separately. Do not submit to the official repository until the security posture and physical testing have been reviewed.

Official references:
- https://contributors.home-assistant.io/apps/reference/configuration/
- https://contributors.home-assistant.io/apps/guides/security/
- https://www.home-assistant.io/common-tasks/os/

## Polski — dystrybucja globalna

**Zakres:** publiczna dystrybucja społecznościowa aplikacji dla Raspberry Pi 5 z Home Assistant OS (min. 18.3) i Home Assistant Core (min. 2026.10.1). Nie oznacza to automatycznej obecności aplikacji w oficjalnym katalogu Home Assistant.

**Instalacja:** dodaj główne repozytorium do sklepu **Apps**, zainstaluj aplikację, następnie zainstaluj oddzielną integrację SBC5 przez HACS/Marketplace. Dodatkowe karty Lovelace są opcjonalne.

**Ostrzeżenie bezpieczeństwa:** aplikacja wymaga wyłączonego Protection Mode oraz szerokich uprawnień do hosta. Home Assistant ocenia `full_access: true` na poziomie bezpieczeństwa **1**. Przed instalacją wykonaj kopię zapasową, sprawdź źródło i udziel dostępu tylko administratorom. To nie jest wersja po niezależnym audycie penetracyjnym.

**Warunki wydania:** zielone testy App/HACS, zgodność wersji 3.2.0, sumy kontrolne, test pakowania i podstawowy test w czystym środowisku CI, bezpieczna aktualizacja **na obecnym Raspberry Pi 5** z wykonaną i sprawdzoną kopią zapasową, sprawdzenie odczytów wentylatora i temperatury przed oraz po aktualizacji, zachowanie stanu AI/kalibracji, przygotowana ścieżka przywracania i poprawne zakończenie aktualizacji HACS/Marketplace. Bez destrukcyjnego testowania awarii wentylatora lub wyłączania wymaganych uprawnień na pracującym urządzeniu.

**Ważne dla aktualizacji sklepowej:** pełna paczka ZIP 3.2.0 RC nie zainstaluje nieopublikowanej wersji runtime na aplikacji zarządzanej przez Apps Store. Służy wyłącznie do sprawdzenia integralności i pakowania — **nie kopiować jej do katalogu automatycznych aktualizacji** działającej aplikacji. Przed publikacją wykonujemy kopię zapasową i zapisujemy odczyty 3.1.37. Test rzeczywistej aktualizacji przez sklep będzie możliwy dopiero, gdy 3.2.0 stanie się dostępne w Apps; wynik sprawdzimy na bieżąco i nie będziemy przedstawiać testu sprzętowego jako ukończonego przed jego wykonaniem.

**Brak drugiego Raspberry Pi 5 nie blokuje publicznego wydania społecznościowego.** Czysta instalacja na drugim fizycznym urządzeniu pozostaje **nieprzetestowana** i musi być tak oznaczona w informacjach o wydaniu. Testy CI nie zastępują fizycznej instalacji. Niezależne testy społeczności można zebrać po publikacji.

**Katalog oficjalny:** osobny proces przeglądu i akceptacji przez opiekunów Home Assistant; dostępność globalna przez własne repozytorium nie oznacza oficjalnej akceptacji.
