# SBC5 Control Center 3.0.0 — Rust Migration

## Status

SBC5 Control Center 3.0.0 introduces the native `sbc5-core` Rust runtime while keeping the proven 2.8.x control plane as a compatibility and safety layer. This is an intentional hybrid architecture: Home Assistant-facing components remain Python/shell where HA integration requires it, while low-overhead host telemetry and runtime health move to Rust.

## Stable 3.0.0 architecture

```text
Home Assistant
    |
    +-- SBC5 integration (Python)
    |
    +-- SBC5 app container
          |
          +-- run.sh                  Rust bootstrap / compatibility hand-off
          +-- sbc5-core               Rust native runtime
          |     +-- host telemetry
          |     +-- per-core CPU usage/frequency
          |     +-- CPU temperature
          |     +-- memory / load / uptime
          |     +-- fan RPM discovery
          |     +-- atomic runtime status
          |
          +-- run_legacy.sh           proven 2.8.x safety/control plane
          +-- ai_cooling.py           compatibility AI engine
          +-- config_ui.py            HA configuration UI
          +-- dashboard_sync.py       HA dashboard synchronization
```

## Why 3.0.0 is hybrid

The fan controller is safety-critical. Replacing the controller, AI learner, host configuration manager and Home Assistant bridge in one release would create unnecessary regression risk. Version 3.0.0 therefore migrates the native runtime boundary first and preserves the existing controller as the authoritative safety layer. Later 3.x releases can move individual controller modules to Rust after parity tests without changing the public HA API.

## Persistence compatibility

The migration does not rename or delete existing `/data` state. CPU/GPU profiles, Adaptive PWM state, AI learning data, update state and user configuration remain compatible with the 2.8.x layout.

New native state:

- `/data/rust_core_status.json`
- `/homeassistant/sbc5_control_center/rust_core_status.json`

The files use schema `1` and are replaced atomically.

## Runtime fallback

At container start, `/usr/local/bin/sbc5-core self-test` is executed. If it succeeds, the Rust daemon starts at a two-second collection interval. If it fails, SBC5 logs the failure and starts the compatibility control plane instead. Native telemetry therefore cannot prevent the fan safety layer from starting.

## Rollback

The 3.0.0 migration does not destructively transform 2.8.x state. Rolling back to the previous stable package leaves the existing `/data` state available. The additional Rust status JSON can be ignored by older versions.

## Native-core commands

```sh
sbc5-core version
sbc5-core self-test
sbc5-core probe
sbc5-core probe --status /data/rust_core_status.json
sbc5-core daemon --status /data/rust_core_status.json \
  --mirror /homeassistant/sbc5_control_center/rust_core_status.json \
  --interval 2
```

## Release gate for 3.0.0

A build can be promoted to stable only when all of the following are true:

1. Rust Core compiles in release mode for `aarch64`.
2. `sbc5-core self-test` exits with code 0 in the HA base container.
3. Native telemetry writes valid status files for at least 30 minutes without growth/leaks.
4. Existing Adaptive PWM safety behavior remains unchanged.
5. Existing AI model and `/data` state survive upgrade and rollback tests.
6. Ingress, dashboard synchronization and the Python HA integration remain functional.
7. Restart/update flows complete without orphaning the native runtime.

---

# SBC5 Control Center 3.0.0 — Migracja do Rust (PL)

Wersja 3.0.0 wprowadza natywny rdzeń `sbc5-core` napisany w Rust. Jest to celowo architektura hybrydowa: elementy wymagające bezpośredniej integracji z Home Assistant pozostają w Pythonie, natomiast lekka telemetria hosta i kontrola zdrowia runtime przechodzą do Rust.

Sterowanie wentylatorem w pierwszej stabilnej wersji 3.0.0 nadal pozostaje w sprawdzonej warstwie kompatybilności 2.8.x. Dzięki temu migracja rdzenia nie zmienia jednocześnie algorytmów bezpieczeństwa Adaptive PWM/AI Cooling.

### Zachowanie danych

Migracja nie usuwa ani nie zmienia nazw istniejących plików `/data`. Zachowane zostają profile CPU/GPU, konfiguracja, stan Adaptive PWM, model AI i dane aktualizacji. Rust dodaje tylko własny status:

- `/data/rust_core_status.json`
- `/homeassistant/sbc5_control_center/rust_core_status.json`

### Tryb awaryjny

Przy starcie wykonywany jest `sbc5-core self-test`. Jeżeli test natywnego rdzenia się nie powiedzie, aplikacja zapisuje błąd w logu i uruchamia dotychczasową warstwę kontrolną. Awaria telemetrii Rust nie może więc zablokować uruchomienia sterowania chłodzeniem.

### Kryterium stabilnego 3.0.0

Build 3.0.0 może zostać oznaczony jako stabilny dopiero po przejściu kompilacji aarch64, testów self-test/runtime, testu zachowania danych 2.8.x, testu upgrade/rollback oraz testów Adaptive PWM, AI Cooling, Ingress i integracji Home Assistant.
