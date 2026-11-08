# SBC5 Control Center

**Wersja 3.1.37 | Raspberry Pi 5 | HA OS 18.3+ | Core 2026.10.1+**

SBC5 monitoruje Raspberry Pi 5, steruje Active Cooler i obsługuje Adaptive PWM, AI Cooling, Thermal Predictor, profile CPU/GPU oraz diagnostykę zasilania i firmware.

## Polski

### Instalacja
Dodaj [repozytorium SBC5](https://github.com/krlmdfk/sbc5-control-center) w Home Assistant Apps i zainstaluj aplikację. Następnie osobno zainstaluj [integrację przez HACS](https://github.com/krlmdfk/sbc5-control-center-integration) i dodaj ją w Ustawienia → Urządzenia i usługi.

### Panel Lovelace
Pełny panel wymaga Mushroom, card-mod i ApexCharts Card z HACS. Same natywne czujniki działają bez tych kart.

### Aktualizacje
Home Assistant Apps obsługuje aktualizacje całej aplikacji ze sklepu. Zweryfikowane paczki ZIP obsługują dostępne scenariusze aktualizacji lokalnych. Mechanizm przejścia Local → Store z SHA-256 i możliwością wycofania zmian istnieje od wersji 2.8.34.

### Dostęp do hosta
Konfiguracja rozruchu, PMIC i diagnostyka firmware mogą wymagać wyłączenia Protection Mode. Gdy dostęp jest ograniczony, SBC5 wstrzymuje zapisy konfiguracji rozruchowej i raportuje ograniczenia.

## English

SBC5 monitors Raspberry Pi 5 and provides Active Cooler, Adaptive PWM, AI Cooling, Thermal Predictor, CPU/GPU profiles and power/firmware diagnostics.

### Installation
Add the [SBC5 App repository](https://github.com/krlmdfk/sbc5-control-center) to Home Assistant Apps and install the App. Then install the separate [HACS integration](https://github.com/krlmdfk/sbc5-control-center-integration) and add it under Settings → Devices & services.

### Lovelace dashboard
The full dashboard additionally needs Mushroom, card-mod and ApexCharts Card from HACS. Native integration sensors do not require these frontend cards.

### Updates and host access
Store-managed full runtime updates use Home Assistant Apps. Verified local ZIPs support local update scenarios. The SHA-256 protected Local → Store handoff with rollback was introduced in version 2.8.34. Boot configuration, PMIC and firmware diagnostics may require Protection Mode disabled.

[Documentation](https://github.com/krlmdfk/sbc5-control-center) | [HACS](https://github.com/krlmdfk/sbc5-control-center-integration) | [Issues](https://github.com/krlmdfk/sbc5-control-center/issues)
