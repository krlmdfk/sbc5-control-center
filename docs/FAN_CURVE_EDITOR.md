# Własna krzywa Active Cooler

SBC5 Control Center używa jednej własnej krzywej `custom1`. Jej ustawienia są przechowywane w konfiguracji aplikacji i stanowią źródło prawdy dla generatora 15 punktów.

## Parametry

Użytkownik ustawia nazwę, temperaturę docelową, histerezę gęstą i zewnętrzną oraz trzy poziomy PWM: minimalny, przy temperaturze docelowej i maksymalny. Generator automatycznie zagęszcza punkty pracy w pobliżu temperatury zadanej, aby sterowanie było bardziej precyzyjne w najważniejszym zakresie.

## Zapis i aktywacja

Po wykryciu zmiany konfiguracji aplikacja generuje `custom1`, zapisuje overlay i ustawia wymagany restart hosta. Stary stan edytora `/data/custom_curve_editor.json` nie może nadpisywać krzywej 1. Dzięki temu wartości zapisane w zakładce **Konfiguracja** pozostają trwałe także po restarcie aplikacji.

Pełny restart Raspberry Pi 5 jest konieczny, ponieważ Device Tree Overlay jest wczytywany podczas startu kernela.
