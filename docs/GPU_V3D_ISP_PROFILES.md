> Build 2.8.15: profile manager and Lovelace GPU preset workflow from 2.8.13 are retained unchanged.

# GPU / V3D / ISP profiles — Raspberry Pi 5

SBC5 Control Center 2.8.13 adds a preset manager for position **22 · CONFIG.TXT — GPU / V3D / ISP**.

Reference clocks published by Raspberry Pi for Pi 5 are: `core_freq=910`, `isp_freq=910`, `v3d_freq=960` MHz and the corresponding minimum clocks are 500 MHz. V3D is independent of core/ISP on Pi 5. Firmware automatically scales voltage when overclocking; the SBC5 GPU presets therefore do not set `over_voltage`.

| Profile | core | ISP | V3D | minima | Use |
|---|---:|---:|---:|---:|---|
| Factory | auto | auto | auto | auto | Recommended default; removes SBC5-owned GPU clock entries. |
| Eco | 850 | 850 | 900 | 500 | Light/headless workloads; lower maximum clocks. |
| Balanced | 950 | 950 | 1000 | 500 | Mild daily OC. |
| Performance | 1000 | 1000 | 1100 | 500 | Higher GPU/V3D performance; test stability and cooling. |
| Experimental | 1100 | 1100 | 1200 | 500 | Not guaranteed stable on every board. |
| Advanced | manual | manual | manual | manual | Manual max/min values with SBC5 safety validation. |

## Advanced mode

Manual protective ranges are 500–1200 MHz for maximum clocks and 200–960 MHz for minimum clocks. SBC5 rejects `*_freq_min > *_freq`. `gpu_freq_min` is retained for compatibility but on Pi 5 individual minimums are preferred.

## Restore defaults

Choose **Factory** or use **Przywróć wartości fabryczne**, save, and allow Config Manager to remove GPU/V3D/ISP entries owned by SBC5. A full Raspberry Pi reboot is required before firmware defaults become active.

No GPU preset changes CPU voltage settings or the Adaptive PWM / AI Cooling algorithms.

## GPU / V3D / ISP z karty Lovelace — 2.8.13

Główna karta SBC5 ma teraz selektor profilu GPU/V3D/ISP oraz przycisk **Zastosuj preset**. Dostępne pozycje:

- **Fabryczny · Auto** — usuwa zarządzane wpisy zegarów GPU i pozostawia wartości firmware,
- **Eco · 850 / 850 / 900 MHz**,
- **Zbalansowany · 950 / 950 / 1000 MHz**,
- **Wydajność · 1000 / 1000 / 1100 MHz**,
- **Eksperymentalny · 1100 / 1100 / 1200 MHz**,
- **Zaawansowany · ustawienia ręczne** — korzysta z wartości wprowadzonych w pozycji 22 Konfiguracji.

Po użyciu przycisku aplikacja zapisuje `config_gpu_profile`, włącza sekcję GPU i Config Manager, wykonuje standardową synchronizację zarządzanego `config.txt` i korzysta z istniejącego mechanizmu backupu/Restart Managera. Jeżeli wynikowy plik boot nie zmienił się, restart nie jest zgłaszany; jeżeli się zmienił, wymagany jest **pełny restart Raspberry Pi 5**. Wybór na karcie synchronizuje się z profilem zapisanym w aplikacji.


### 2.8.15 — trwałość profilu GPU po restarcie
Wybrany profil GPU/V3D/ISP jest zapisywany niezależnie w `/data/gpu_profile_state.json`. Po pełnym restarcie hosta ten stan ma pierwszeństwo przed przejściową wartością domyślną `factory` z opcji Supervisor. Przy aktualizacji z 2.8.12–2.8.14, jeśli pliku stanu jeszcze nie ma, aplikacja rozpoznaje preset zapisany wcześniej w `sbc5cc-managed.txt` i importuje go jako żądany profil.
