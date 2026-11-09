# SBC5 3.2.1 — Hardware acceptance / Odbiór sprzętowy

Status: **NOT VERIFIED** until all actual-device fields below have evidence.
Release PR: https://github.com/krlmdfk/sbc5-control-center/pull/69
Offline rehearsal: https://github.com/krlmdfk/sbc5-control-center/actions/runs/42657828426

This checklist is for the owner/operator of the real Raspberry Pi 5. It is
**not** a claim that testing has happened. Do not publish 3.2.1, mark
\`hardware_verified=true\`, or run the offline rehearsal ZIP as an update
until this record has been completed and independently checked.

## 1. Przed zmianami / Before changes

- [ ] Zanotowano faktyczną wersję App, identyfikator instalacji (slug) i wersję HAOS/Core.
- [ ] Wykonano pełną kopię Home Assistant, obejmującą dane aplikacji; potwierdzono możliwość odtworzenia.
- [ ] Utrwalono niezależną kopię \`/data/ai_cooling_model.json\` z właściwego **kontenera App**, a nie z ogólnego terminala HAOS.
- [ ] Zweryfikowano odczyt JSON i SHA-256 kopii modelu; zanotowano wersję schematu, licznik wszystkich obserwacji i próbek jakościowych.
- [ ] Zanotowano profil CPU/GPU, krzywą i temperaturę docelową, Adaptive PWM i aktualne parametry chłodzenia.
- [ ] Potwierdzono działanie fizycznego chłodzenia oraz możliwość bezpiecznego przywrócenia poprzedniej wersji.

Evidence / Dowody (no secrets or full AI model uploaded publicly):
- App version/slug: **NOT VERIFIED**
- HAOS/Core: **NOT VERIFIED**
- Backup identifier and verified restore location: **NOT VERIFIED**
- Model SHA-256 / schema / total / qualified: **NOT VERIFIED**
- Fan safety/control baseline: **NOT VERIFIED**

## 2. Izolowana kontrola / Isolated check

- [ ] Izolowany Canary z PR #68 uruchomiono tylko ręcznie, bez dostępu do GPIO, HA API ani prywatnego \`/data\` aplikacji produkcyjnej.
- [ ] Pakiet 3.2.1 przechodzi walidację manifestu i SHA-256 w odizolowanej instancji.
- [ ] Sprawdzono niezależną kopię modelu AI bez jej modyfikacji.
- [ ] Stabilna aplikacja i rzeczywisty wentylator zachowują dotychczasowe działanie.

## 3. Aktualizacja kontrolowana / Controlled hardware upgrade

**Only after all previous gates are met and a hardware maintenance plan has been approved.**
The offline rehearsal archive is **NOT INSTALLABLE**.

- [ ] Dopuszczono do instalacji osobno podpisany/zweryfikowany pakiet wydania (commit + SHA-256 + sposób odtworzenia).
- [ ] Sprawdzono wersję 3.2.1 i zakres konfiguracji przed pierwszym uruchomieniem.
- [ ] Potwierdzono zachowanie modelu AI i liczników po restarcie App oraz po restarcie Home Assistant.
- [ ] Potwierdzono temperaturę CPU, bezpieczeństwo wentylatora i Adaptive PWM w normalnej pracy, bez prowokowania awarii.
- [ ] Potwierdzono profile CPU/GPU, krzywą \`custom1\`, temperaturę docelową i nastawy regulatora.
- [ ] Potwierdzono synchronizację Card UI 3.2.1 i integracji HACS.
- [ ] Nie wystąpiły nieoczekiwane zmiany konfiguracji hosta, przejęcie właściciela PWM ani błędy migracji.

## 4. Przywracanie / Rollback

- [ ] Potwierdzono scenariusz przywrócenia poprzedniego App i jego danych (najpierw w odizolowanym środowisku).
- [ ] Potwierdzono możliwość odtworzenia kopii modelu AI bez używania przycisku \`reset_ai_model\`.
- [ ] Udokumentowano stan, w którym należy przerwać test (temperatura, zachowanie wentylatora, błędy modelu lub migracji).
- [ ] Porównano dane po przywróceniu z oryginalnymi hashami i konfiguracją.

## 5. Publication / Publikacja

- [ ] Main candidate has green Validate build, Rust Core CI, Companion parity audit.
- [ ] Offline release rehearsal has green App ↔ HACS parity, strict manifest and ZIP preflight.
- [ ] HACS 3.2.1 is prepared and validation is green on its own candidate.
- [ ] Wszystkie testy sprzętowe są potwierdzone dowodami przez operatora.
- [ ] Nadano świadomą zgodę na wydanie 3.2.1 wraz z aktualizacją HACS.

Only after all boxes are checked may the controlled manual release workflow be
run with \`dry_run=false\` and \`hardware_verified=true\`. This approval cannot
be inferred from CI alone.

**Final state: BLOCKED — awaiting actual Raspberry Pi 5 hardware evidence.**
