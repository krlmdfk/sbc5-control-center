# SBC5 Control Center 1.9.10 — referencja `config.txt`

> Szybka referencja parametrów dostępnych w **Konfiguracja → CONFIG.TXT**. Do codziennej pracy zaczynaj od `auto`; wartość ręczną ustawiaj tylko wtedy, gdy chcesz świadomie przejąć kontrolę nad danym parametrem.

## Jak korzystać z tej referencji

- `auto` — Control Center **nie tworzy** wpisu dla danego parametru.
- **Zakres ochronny aplikacji** — zakres przyjmowany w trybie standardowym; Tryb zaawansowany może pozwolić na więcej.
- **Pełny restart RPi5** — wymagany po zmianach `config.txt`, ponieważ plik jest odczytywany podczas startu.
- Parametry dynamiczne, `dtoverlay`, `dtparam` i `include` dodawaj w sekcji **Własne parametry**.

## Bezpieczny model zapisu

1. Główny `config.txt` pozostaje plikiem systemu/użytkownika.
2. Control Center utrzymuje własny `rpi5cc-managed.txt` i dodaje kontrolowany wpis `include`.
3. Przed zmianą tworzony jest backup.
4. Walidacja i wykrywanie konfliktów mogą zablokować niebezpieczny zapis.
5. Tryb zaawansowany nie wyłącza podstawowej walidacji składni.

## Poziomy ryzyka

| Poziom | Znaczenie |
|---|---|
| **niski** | zwykle nie wpływa na możliwość startu systemu |
| **średni** | może zmienić zachowanie sprzętu lub interfejsów |
| **wysoki** | może powodować niestabilność, problemy z boot lub wymagać ręcznego przywrócenia konfiguracji |

## Sekcje `config.txt`

Najczęściej używane filtry to `[pi5]`, `[all]` i `[none]`. W polu sekcji wpisuj nazwę **bez nawiasów**, np. `pi5`, `all`, `tryboot`.

## CPU / overclocking

| Parametr | Typ | Domyślnie | Zakres / wartości | Ryzyko | Opis |
|---|---|---:|---|---|---|
| `arm_freq` | `int` | `2400` | aplikacja: 1500–2800; profil domyślny: 2400 MHz | wysoki | Maksymalna częstotliwość CPU ARM. Domyślnie Pi 5: 2400 MHz. |
| `arm_freq_min` | `int` | `1500` | 600–2400 (obniżanie poniżej domyślnej nie jest zalecane) | wysoki | Minimalna częstotliwość CPU używana przez dynamiczne skalowanie. Domyślnie Pi 5: 1500 MHz. |
| `over_voltage` | `int` | `0` | -16–8; krok odpowiada 0,025 V | wysoki | Górny limit napięcia CPU/GPU core według skali firmware. |
| `over_voltage_min` | `int` | `0` | -16–8 | wysoki | Minimalna wartość over_voltage; na Pi 4/Pi 5 parametr jest przestarzały. **Uwaga:** Deprecated na Raspberry Pi 4 i Raspberry Pi 5. |
| `over_voltage_delta` | `int` | `0` | µV; firmware nie publikuje jednego twardego maksimum; Control Center: 0–50000 w profilu bezpiecznym | wysoki | Pi 4/Pi 5: dodaje offset do napięcia wyliczonego przez DVFS. |
| `force_turbo` | `bool` | `0` | `0` / `1` | wysoki | Wymusza tryb turbo zamiast dynamicznego skalowania. |
| `initial_turbo` | `int` | `0` | 0–60 | wysoki | Czas po starcie, przez który firmware utrzymuje turbo. |

## CPU / termika

| Parametr | Typ | Domyślnie | Zakres / wartości | Ryzyko | Opis |
|---|---|---:|---|---|---|
| `temp_limit` | `int` | `85` | 0–85 | wysoki | Próg ochrony termicznej; wartości powyżej 85°C są ograniczane do 85°C. |

## GPU / zegary

| Parametr | Typ | Domyślnie | Zakres / wartości | Ryzyko | Opis |
|---|---|---:|---|---|---|
| `core_freq` | `int` | `910` | 500–1200 (zakres ochronny aplikacji) | wysoki | Częstotliwość core. Domyślnie Pi 5: 910 MHz. |
| `isp_freq` | `int` | `910` | 500–1200 (zakres ochronny aplikacji) | wysoki | Częstotliwość bloku ISP. Domyślnie Pi 5: 910 MHz. |
| `v3d_freq` | `int` | `960` | 500–1200 (zakres ochronny aplikacji) | wysoki | Częstotliwość bloku V3D. Domyślnie Pi 5: 960 MHz. |
| `core_freq_min` | `int` | `500` | 200–910 | wysoki | Minimalna częstotliwość core. Domyślnie Pi 5: 500 MHz. |
| `gpu_freq_min` | `int` | `500` | 200–960 | wysoki | Minimalna częstotliwość grupy GPU; na Pi 5 część bloków ma niezależne zegary. |
| `isp_freq_min` | `int` | `500` | 200–910 | wysoki | Minimalna częstotliwość ISP. Domyślnie Pi 5: 500 MHz. |
| `v3d_freq_min` | `int` | `500` | 200–960 | wysoki | Minimalna częstotliwość V3D. Domyślnie Pi 5: 500 MHz. |

## Zasilanie / USB

| Parametr | Typ | Domyślnie | Zakres / wartości | Ryzyko | Opis |
|---|---|---:|---|---|---|
| `usb_max_current_enable` | `bool` | — | `0` / `1` | wysoki | Wymusza niski lub wysoki sprzętowy limit prądu portów USB-A: 0≈600 mA, 1≈1600 mA. **Uwaga:** Auto = brak wpisu. Wysoki limit tylko przy zasilaniu zdolnym dostarczyć 5 A. |

## Zasilanie

| Parametr | Typ | Domyślnie | Zakres / wartości | Ryzyko | Opis |
|---|---|---:|---|---|---|
| `power_force_3v3_pwm` | `bool` | `0` | `0` / `1` | wysoki | Pi 5: wymusza PWM na wyjściu 3,3 V GPIO/CSI. |

## PCIe / RP1

| Parametr | Typ | Domyślnie | Zakres / wartości | Ryzyko | Opis |
|---|---|---:|---|---|---|
| `pciex4_reset` | `bool` | `1` | `0` / `1` | wysoki | Pi 5: określa, czy kontroler PCIe x4 używany przez RP1 jest resetowany przed startem systemu. |

## Boot / kernel

| Parametr | Typ | Domyślnie | Zakres / wartości | Ryzyko | Opis |
|---|---|---:|---|---|---|
| `auto_initramfs` | `bool` | `1` | `0` / `1` | niski | Automatycznie ładuje initramfs, jeśli firmware go znajdzie. |
| `arm_64bit` | `bool` | `1` | `0` / `1` | średni | Wybiera 64-bitowy tryb kernela, gdy dostępny. |
| `boot_ramdisk` | `bool` | `0` | `0` / `1` | wysoki | Próbuje uruchomić boot filesystem z boot.img (głównie secure boot / netboot). |
| `set_reboot_arg1` | `uint32` | — | 0–4294967295 | średni | Pi 5: zapisuje 32-bitową wartość przekazywaną przez restart-safe register. |
| `kernel` | `string` | `kernel_2712.img` | nazwa pliku, maks. 90 znaków | wysoki | Alternatywna nazwa pliku kernela. Pi 5 domyślnie preferuje kernel_2712.img. |
| `cmdline` | `string` | `cmdline.txt` | nazwa pliku, maks. 90 znaków | wysoki | Alternatywna nazwa pliku z linią poleceń kernela. |
| `os_prefix` | `string` | — | ścieżka względna, maks. 90 znaków | wysoki | Prefix katalogu systemowego stosowany do plików boot. |

## Boot / debug

| Parametr | Typ | Domyślnie | Zakres / wartości | Ryzyko | Opis |
|---|---|---:|---|---|---|
| `sha256` | `bool` | `0` | `0` / `1` | niski | Włącza logowanie SHA-256 ładowanych plików boot; może wyraźnie wydłużyć start. |

## Sprzęt / autodetekcja

| Parametr | Typ | Domyślnie | Zakres / wartości | Ryzyko | Opis |
|---|---|---:|---|---|---|
| `camera_auto_detect` | `bool` | `1` | `0` / `1` | niski | Automatycznie ładuje overlay dla rozpoznanych kamer CSI. |
| `display_auto_detect` | `bool` | `1` | `0` / `1` | niski | Automatycznie ładuje overlay dla rozpoznanych wyświetlaczy DSI. |

## UART / debug

| Parametr | Typ | Domyślnie | Zakres / wartości | Ryzyko | Opis |
|---|---|---:|---|---|---|
| `enable_uart` | `bool` | `0` | `0` / `1` | średni | Włącza podstawowy UART; na rodzinie Pi 5 wpływa również na lokalizację konsoli. |
| `enable_rp1_uart` | `bool` | `0` | `0` / `1` | średni | Pi 5: inicjalizuje RP1 UART0 115200 bps dla wczesnego debugowania. |
| `uart_2ndstage` | `bool` | `0` | `0` / `1` | średni | Włącza logowanie debug bootu do UART w drugim etapie. |

## Device Tree

| Parametr | Typ | Domyślnie | Zakres / wartości | Ryzyko | Opis |
|---|---|---:|---|---|---|
| `device_tree` | `string` | — | nazwa pliku .dtb, maks. 90 znaków | wysoki | Wskazuje alternatywny bazowy plik Device Tree (.dtb). |
| `overlay_prefix` | `string` | `overlays/` | ścieżka względna, maks. 90 znaków | wysoki | Katalog/prefix, z którego firmware ładuje overlaye. |
| `dtparam` | `directive` | — | dynamiczny; overlays/README / dtoverlay -h | średni | Parametr bazowego Device Tree lub aktywnego overlaya. Dostępne nazwy i zakresy zależą od zainstalowanego DT/overlaya. |
| `dtoverlay` | `directive` | — | dynamiczny; nazwa overlaya + opcjonalne parametry | wysoki | Ładuje Device Tree overlay. Lista i parametry zależą od obrazów .dtbo zainstalowanych w systemie. |

## Wideo / ekran

| Parametr | Typ | Domyślnie | Zakres / wartości | Ryzyko | Opis |
|---|---|---:|---|---|---|
| `enable_tvout` | `bool` | `0` | `0` / `1` | średni | Włącza wyjście composite; na Pi 5 wyłącza HDMI. |
| `disable_overscan` | `bool` | `1` | `0` / `1` | niski | Wyłącza kompensację overscan. |

## Wideo / KMS

| Parametr | Typ | Domyślnie | Zakres / wartości | Ryzyko | Opis |
|---|---|---:|---|---|---|
| `disable_fw_kms_setup` | `bool` | `1` | `0` / `1` | średni | Nie pozwala firmware tworzyć początkowego ustawienia video= dla KMS. |
| `max_framebuffers` | `int` | `2` | 0–2 | średni | Maksymalna liczba firmware framebufferów. |

## CPU / compatibility

| Parametr | Typ | Domyślnie | Zakres / wartości | Ryzyko | Opis |
|---|---|---:|---|---|---|
| `arm_boost` | `bool` | `0` | `0` / `1` | średni | Podnosi domyślny turbo zegar na wybranych Pi 4/400; nie jest potrzebny do Pi 5. |

## Wideo / compatibility

| Parametr | Typ | Domyślnie | Zakres / wartości | Ryzyko | Opis |
|---|---|---:|---|---|---|
| `hdmi_enable_4kp60` | `bool` | `0` | `0` / `1` | średni | Pi 4/400/CM4: zezwala na 4Kp60. Pi 5 obsługuje dual-4Kp60 bez tego wpisu. |

## Audio / legacy

| Parametr | Typ | Domyślnie | Zakres / wartości | Ryzyko | Opis |
|---|---|---:|---|---|---|
| `audio_pwm_mode` | `int` | — | legacy/model-dependent | średni | Tryb firmware PWM dla analogowego audio; nie jest typowym parametrem Pi 5. |

## Zaawansowane

| Parametr | Typ | Domyślnie | Zakres / wartości | Ryzyko | Opis |
|---|---|---:|---|---|---|
| `include` | `directive` | — | ścieżka względna do pliku, maks. 90 znaków | wysoki | Włącza treść dodatkowego pliku config do bieżącej konfiguracji. |

## Device Tree: parametry dynamiczne

`dtoverlay` i `dtparam` nie mają jednej zamkniętej listy zakresów. Dostępne overlaye i ich argumenty zależą od plików `.dtbo` zainstalowanych w obrazie systemu. Control Center dlatego traktuje te dyrektywy jako powtarzalne i pozwala wprowadzić dokładną nazwę/wartość. Docelowym źródłem zakresu jest lokalny `overlays/README` oraz pomoc `dtoverlay -h <nazwa>`.

## Parametry spoza katalogu

Każdy syntaktycznie poprawny parametr może zostać dodany w **Trybie zaawansowanym**. Dla takiego parametru aplikacja pokazuje zakres ogólny: pojedyncza wartość tekstowa do 90 znaków i łączny limit wpisu 98 znaków. Brak katalogowego zakresu oznacza, że Control Center nie potrafi ocenić poprawności semantycznej parametru.

## Źródła zakresów

- Raspberry Pi Documentation — `config.txt` (wartości domyślne, filtry, overclocking, boot).
- Raspberry Pi Documentation — konfiguracja / Device Tree overlays.
- Zakresy opisane jako **ochronne aplikacji** są celowo węższe od teoretycznych możliwości firmware i mogą być ominięte tylko w Trybie zaawansowanym.

