# SBC5 3.2.0 — Host permission audit / Audyt uprawnień hosta

> Static review of App config and representative runtime files on 2026-11-08. This does **not** prove that each privilege is minimally necessary. No hardware privilege reduction is deployed in 3.2.0 without regression tests.

## Current declarations and review

| Permission / access | Capability and risk | Evidence in project / why investigated | 3.2.0 decision |
|---|---|---|---|
| `full_access: true` | Access to all host devices; Home Assistant security score forced to 1 | Host-oriented config.txt, firmware/PMIC and cooling/boot access; config.yaml and run_legacy.sh | **Retain temporarily, openly disclose, prioritize least-privilege redesign** |
| `host_pid: true` | Access host PID namespace; requires Protection Mode off | ethernet_guard.py accesses `/proc/1/root/...`; boot-path discovery depends on host view | **Retain for compatibility; physical test needed before removal** |
| `apparmor: false` | Disables additional filesystem/process sandbox | Broad host access, boot file discovery and legacy runtime | **Audit and develop custom AppArmor profile before changing** |
| `SYS_ADMIN` | Broad kernel capability | Declared in config.yaml; necessity for each runtime operation not proven | **Audit required; do not silently remove** |
| `SYS_PTRACE` | Process tracing/inspection capability | Declared in config.yaml; direct functional need not established by this audit | **Least-privilege candidate, test before removal** |
| `hassio_role: manager` + Supervisor API | Can manage installed apps and Supervisor operations | namespace_native_guard.sh handles App listing/migration; historical release notes cite reload/rebuild | **Retain until update/migration flows tested with lower role** |
| `homeassistant_api: true` | API calls to Home Assistant Core | Home Assistant sensor/config integration and migration verification | **Retain pending scoped API review** |
| `homeassistant_config:rw` | May modify Home Assistant configuration files | App migration/package, dashboard and relay synchronization | **Reduce to narrower ownership in future design** |
| `local_apps:rw` | May write local App store files | Historic Local → Store migration and local update manager | **Retain pending migration test** |
| `app_config:rw` / `/config` | Writes App-specific configuration | App UI/management configuration and saved state | **Expected App-owned writable storage** |

## Security consequences

- Home Assistant's documentation says `full_access` gives the lowest security rating (1); it is **not a vulnerability finding by itself**, but compromises isolation if a component is exploited.
- Protection Mode on disables host-level access requested by `full_access` and `host_pid`. SBC5 documentation already requires it off for host functionality.
- Do not claim Home Assistant endorses SBC5 or that acceptance into HACS equals App security review.
- Admin-only access, trusted installation source, backups and published update hash verification are required operational precautions.
- Reduce privileges in a future tested change: inventory syscalls/device paths and Supervisor endpoints, partition read-only telemetry from host boot/config writes where possible, then test a custom AppArmor profile and narrower mounts.

## Specific tests before least-privilege changes

1. Read CPU temperature/fan RPM/PWM with Protection Mode on/off and verify degraded status when access is absent; never allow unbounded fan commands.
2. Check CPU/GPU boot profiles and `config.txt` backup/restore and rollback across a reboot.
3. Verify PMIC and firmware/EEP/network telemetry on Raspberry Pi 5 without process-namespace assumptions.
4. Test Supervisor App reload/rebuild, migration, backups, HACS ownership and update handoff.
5. Test graceful behavior when file paths, APIs or privileges are unavailable.
6. Review all privileged paths with another maintainer before making the change default.

## Polish summary / Podsumowanie

Obecna konfiguracja wymaga szerokich uprawnień systemowych, a `full_access` oznacza ocenę bezpieczeństwa 1. Uzasadnienia opisują znane ścieżki funkcjonalne, ale **nie potwierdzają minimalności każdego uprawnienia**. W 3.2.0 dokumentujemy ryzyko i plan ograniczenia uprawnień; nie zmieniamy ich bez testów sprzętowych.

Official reference: https://contributors.home-assistant.io/apps/guides/security/
