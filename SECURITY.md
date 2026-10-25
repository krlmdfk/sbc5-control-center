# Security Policy

## Zgłaszanie podatności

Jeżeli problem dotyczy bezpieczeństwa, nie publikuj w zgłoszeniu publicznym sekretów, tokenów ani danych umożliwiających dostęp do systemu Home Assistant.

W raporcie bezpieczeństwa podaj minimalny zestaw informacji potrzebnych do odtworzenia problemu: wersję projektu, wersję Home Assistant, wektor problemu i spodziewany wpływ.

## Zakres szczególnego ryzyka

SBC5 Control Center może wykonywać uprzywilejowane operacje dotyczące konfiguracji hosta. Zmiany w obsłudze `config.txt`, restartów, ścieżek plików, aktualizacji ZIP i walidacji symlinków powinny być traktowane jako kod wymagający szczególnie dokładnego review.
