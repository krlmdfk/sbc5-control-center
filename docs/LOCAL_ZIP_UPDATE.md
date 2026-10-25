# Lokalne aktualizacje ZIP

Od 2.8.13 obowiązuje wspólne wersjonowanie App + Card UI. Skaner wybiera wyłącznie pełne wydania `update_scope: full`.

Wymagania manifestu:
- `version`, `package_version` i `card_ui_version` muszą być identyczne;
- wszystkie pliki są weryfikowane SHA-256;
- `restart_required` może być `none`, `home_assistant` lub `host`;
- paczki `dashboard_only` / `ui_only` są odrzucane, aby nie dopuścić do rozjazdu numerów wersji.

Po starcie pełnego buildu aplikacja usuwa niezależny override UI i próbuje bezpiecznie zsynchronizować pojedynczą kartę Lovelace z kartą dostarczoną przez build.
