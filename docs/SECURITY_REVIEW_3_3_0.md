# SBC5 3.3.0 — preliminary security posture review

Review date: 2026-11-18. Scope: source repository and published configuration, **not** a full CVE or running-container vulnerability scan.

## Findings / limitations

| Priority | Finding | Evidence | Action |
|---|---|---|---|
| High | The App requests broad host privileges | `config.yaml`: `full_access: true`, `apparmor: false`, `host_pid: true`, `SYS_ADMIN`, `SYS_PTRACE`, `hassio_role: manager` and writable host-facing mounts | Independently audit capabilities and file access; migrate toward least privilege only after comprehensive Raspberry Pi 5 / HA OS hardware tests. |
| High | Rust builder base uses an unsupported Alpine branch | `Dockerfile`: `rust:1.85-alpine3.21`; Alpine 3.21 support ended on 2026-11-01. **This is a build stage**, not the shipped runtime image | Move build to an officially supported Rust+Alpine image following cross-architecture reproducible builds and hardware verification. |
| Medium | Supply-chain updates were not automated | There was no `.github/dependabot.yml` in `main` before 3.3.0 | Added weekly Docker, GitHub Actions and Cargo Dependabot checks in this PR. |
| Medium | Runtime image is pinned only to release family, not a verified digest | `Dockerfile`: `ghcr.io/home-assistant/base:3.24` | Keep the supported Home Assistant base patched; consider digest pinning with automated updates and test the rebuilt image. |
| Medium | No demonstrated vulnerability scan of the released image | No audited full filesystem/SBOM scan result is provided in this PR | Add Trivy/Grype or equivalent image scans, SBOM generation and high/critical vulnerability triage to release gate; inspect each result before claims of CVE remediation. |
| Low / positive | Ingress request and ZIP boundaries already tested | `scripts/test_config_ui_request_limits_3_2_1.py` and ZIP preflight validators | Preserve tests; re-test on every code change. |
| Low / positive | Rust project has no external Cargo crates at present | `rust-core/Cargo.lock` only lists `sbc5-core` | Continue checking compiler, base image and system packages; absence of external crates does **not** establish CVE-free build. |

## 3.3.0 diagnostic tab security boundary

The grouped view is read-only. `/api/diagnostics/entities` inherits the existing Home Assistant Ingress peer gate; the backend uses the existing Supervisor credential for a fixed Core API URL with a 5s timeout. It returns only allowlisted `sensor.sbc5_*` / `binary_sensor.sbc5_*` entity IDs, names, current states and units, capped at 600 entries; unrelated entities and all other attributes are excluded. The frontend uses `textContent` instead of injecting sensor-provided HTML. It creates no service calls or write action and only polls while the diagnostics tab is visible.

## Result

**Status: security posture partially verified, NOT certified CVE-free.** Successful CI tests establish only their tested properties. A complete claim of up-to-date CVE remediation requires an actual versioned image/SBOM scan, base-image rebuild assessment, verification of repository Dependabot alerts and privileged-operation review.

Reference documentation:
- Alpine release lifecycle: https://www.alpinelinux.org/releases/
- HA App security: https://contributors.home-assistant.io/apps/guides/security/
- HA security rating: https://contributors.home-assistant.io/apps/reference/security-rating/
