# SBC5 Rust Canary 3.0.0

This branch exposes an isolated Home Assistant App identity for real-device migration testing.

- Supervisor slug: `rust_canary_sbc5_control_center`
- Version: `3.0.0`
- Stage: `experimental`
- Boot policy: `manual`
- Stable source remains authoritative until it exports a verified schema-2 handoff.
- Never run the stable controller and the canary controller concurrently.
- Do not merge the canary slug/configuration into the stable release branch.

The canary exists only to validate preserved-state migration, Rust startup, Host Access, CPU/GPU profile reconciliation, Adaptive PWM/AI parity and rollback on Raspberry Pi 5 / HAOS.
