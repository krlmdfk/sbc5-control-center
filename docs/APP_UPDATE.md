# Aktualizacje SBC5 Control Center

## Unified release versioning — od 2.8.13
Jedno wydanie ma jeden numer wersji dla runtime aplikacji, package/integracji i Card UI.
Manifest pełnego buildu musi spełniać `version == package_version == card_ui_version`.

Osobno wersjonowane paczki `dashboard_only` / `ui_only` nie są publikowane ani instalowane, ponieważ powodowały rozjazd wersji App/Card UI. Każda poprawka kart jest od tej wersji dostarczana jako kolejny pełny build.

Pełny build może wymagać restartu Home Assistant zgodnie z `restart_required`; restart Raspberry Pi jest wymagany tylko dla `restart_required: host`.

## Cooling-aware Phase B — od 2.8.15
Phase B nie sprawdza już wyłącznie relay/bridge/encje. Jeżeli użytkownik ma zapisany `custom1`, finalizacja aktualizacji wymaga także aktywnej siatki 1% (`max_state>=100`). Przy rozjeździe profilowym ZIP i backup pozostają zachowane, a Fan Profile Reconciliation naprawia brakujące artefakty boot bez pętli ponownych zapisów.
