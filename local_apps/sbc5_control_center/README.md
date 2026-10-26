<p align="center">
  <a href="https://github.com/krlmdfk/sbc5-control-center">
    <img src="logo.png" alt="SBC5 Control Center" width="160">
  </a>
</p>

# SBC5 Control Center App/runtime

**[English](README.en.md)** · **[Polski](README.pl.md)** · **[Main project](https://github.com/krlmdfk/sbc5-control-center)** · **[HACS integration](https://github.com/krlmdfk/sbc5-control-center-integration)**

The SBC5 Control Center App/runtime is the host-side component of the SBC5 project for Raspberry Pi 5 and Home Assistant OS. It provides cooling control, hardware telemetry, AI Cooling, hardware profiles, managed boot configuration, update handling and Restart Manager services consumed by the native Home Assistant integration.

Aplikacja/runtime SBC5 Control Center jest hostową częścią projektu SBC5 dla Raspberry Pi 5 i Home Assistant OS. Zapewnia sterowanie chłodzeniem, telemetrię sprzętową, AI Cooling, profile sprzętowe, zarządzanie konfiguracją boot, aktualizacje oraz Restart Manager wykorzystywany przez natywną integrację Home Assistant.

> The HACS integration is a companion component and requires this App/runtime to be installed and running.
>
> Integracja HACS jest komponentem towarzyszącym i wymaga zainstalowanej oraz uruchomionej tej aplikacji/runtime.

## Install from Home Assistant Apps / Instalacja ze sklepu Apps

**English:** Home Assistant → **Settings → Apps → Install app → ⋮ → Repositories** → add `https://github.com/krlmdfk/sbc5-control-center` → refresh the store → install **SBC5 Control Center**.

**Polski:** Home Assistant → **Ustawienia → Apps → Install app / Zainstaluj aplikację → ⋮ → Repositories / Repozytoria** → dodaj `https://github.com/krlmdfk/sbc5-control-center` → odśwież sklep → zainstaluj **SBC5 Control Center**.

The HACS integration is installed separately from `https://github.com/krlmdfk/sbc5-control-center-integration`. / Integrację HACS instaluje się osobno z `https://github.com/krlmdfk/sbc5-control-center-integration`.

For full project documentation, use the main repository: **https://github.com/krlmdfk/sbc5-control-center**.


## Lovelace / dashboard dependencies

For the complete dashboard install through HACS: **Mushroom**, **card-mod**, and **ApexCharts Card**. / Dla kompletnego dashboardu zainstaluj przez HACS: **Mushroom**, **card-mod** i **ApexCharts Card**.


## Hybrid update channel / Hybrydowy kanał aktualizacji

Store-managed SBC5 uses Home Assistant Apps as the canonical full-runtime update channel. Verified local ZIPs remain supported for UI-only updates and, for a Store installation, may trigger the native Apps update when the exact same version is published. Historical local installations retain direct full-ZIP rebuilds. The 2.8.31 Migration Manager provides a SHA-256-protected Local → Store handoff with rollback.

Instalacja sklepowa SBC5 używa Home Assistant Apps jako kanonicznego kanału pełnych aktualizacji runtime. Zweryfikowane lokalne ZIP-y pozostają obsługiwane dla UI-only, a w instalacji sklepowej mogą wyzwolić natywną aktualizację Apps, gdy identyczna wersja jest opublikowana. Historyczna instalacja lokalna zachowuje bezpośrednie pełne przebudowy ZIP. Migration Manager 2.8.31 zapewnia handoff Local → Store zabezpieczony SHA-256 i rollback.
