# SBC5 AI Cooling — capability and isolation threat model (3.2.1 candidate)

Status: **static code review only; not a proof of isolation**. SBC5 3.2.0 installations are unchanged.

## Scope and output authority

- AI Cooling v5.2 is a local numerical learner, **not** a generative/autonomous agent.
- It predicts a bounded fan PWM adjustment; the Adaptive PWM controller remains the only intended writer to the fan's `cur_state`.
- Thermal Predictor only influences the bounded AI-assist path. It does not have its own fan-control loop.
- The final Adaptive PWM loop applies min/max limits, a curve corridor, slew-rate limits, owner checks and a thermal safety override.
- AI modules have no network client, subprocess runner, plugin discovery, or external task/action dispatcher in the reviewed files.
- These observations do **not** mean an attacker who can modify the privileged App's scripts or root-owned data cannot change behavior. Host/root compromise remains out of scope of code-only guards.

## Findings and exposure

| Data/action | Current source/storage | Trust boundary | Consequence |
| --- | --- | --- | --- |
| Model training state | `/data/ai_cooling_model.json` | App-private persistent data, but no separate unprivileged AI worker | Model can be edited by App itself or sufficiently privileged host process |
| Training telemetry | `/homeassistant/sbc5_control_center/telemetry.json` | Writable HA configuration shared with other software | A third-party integration/App with HA config write access could tamper with telemetry and bias model learning |
| AI status mirror | `/homeassistant/sbc5_control_center/ai_cooling.json` | Public/compat mirror in HA config | May be altered without changing primary model, but is unsuitable as a trusted control input |
| AI reset | Ingress `/api/reset_ai_model` | Privileged configuration server | An unauthorized caller could destroy learned model state if reachable |
| CPU heat/load | Physical host | Ordinary other apps can consume CPU | Model must respond to genuine CPU workload; this is *physical influence*, not model takeover |
| Fan control | Adaptive PWM final actuator writer | Shared host thermal device | Other privileged code may still write device state; SBC5 reasserts ownership when detected, not a host-wide exclusive hardware lock |

## Security hardening steps

1. **Ingress:** Restrict configuration HTTP requests to TCP source IP `172.30.32.2` (HA Supervisor proxy), as recommended by HA developer documentation. This is proposed in App PR #53; verify live Ingress before merging. HTTP headers alone are not proof of origin.
2. **Separate training data:** Write an atomic, schema-validated, App-private AI telemetry snapshot in `/data`. Keep existing shared HA telemetry for dashboards; migrate AI input from the shared path in a separately tested PR. Reject stale, non-finite or out-of-range values. Test preserved prediction quality and restart behavior.
3. **Model integrity:** Use strict private-directory permissions and fail-closed-on-corruption model validation; prevent silent model resets during transient failures. Coordinate the reset endpoint with active model writes. File checksums alone do not protect against privileged attackers able to rewrite both model and checksum.
4. **Least privilege:** In a subsequent hardware-tested architecture, move the numerical AI worker into a separate unprivileged process with no network, Supervisor token, host mounts or fan device access. It should return a validated *numeric PWM suggestion only*. Limit CPU/IO resources and model storage rights.
5. **Control gateway:** Keep all fan writes in Adaptive PWM with a strict numeric schema, bounded corrections, target/rate/thermal guards, timeout, safe fallback and rejection logging. Test malicious/non-finite/oversized/stale AI responses and corrupted state.
6. **Privilege review:** The current parent App uses `full_access: true`, `host_pid: true`, `apparmor: false` and Supervisor manager privileges. These are not suitable as proof of isolation. Changing them without Pi5 regression could break boot, cooling or migration.
7. **Continuous tests:** CI includes static checks against network/process imports and direct fan control from AI modules; these are regression tripwires, not a security sandbox.

## Acceptance conditions before claiming strong isolation

- Other non-privileged Home Assistant Apps cannot write the primary AI model *or* its private training input, even if they can alter the dashboard mirror.
- Untrusted HA telemetry mirror edits do not change training input.
- Untrusted or corrupt model state does not become an arbitrary host action.
- AI cannot directly access Supervisor API, shell/process execution or the fan actuator.
- Safety/critical temperature handling is independent of the model.
- Live tests on a Raspberry Pi 5 confirm correct cooling, safe degraded operation and no regression after HA restart, App restart and update.
- An App with arbitrary host/root privileges cannot be isolated by Python-level checks alone; OS-level privileges and host trust remain critical.

**Verdict:** Model scope is narrow by design, but complete protection against influence from every other App is **not demonstrated**. Work on a private training input and lower-privilege AI worker remains necessary.
