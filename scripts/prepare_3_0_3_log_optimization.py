#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
RUN = APP / "run_legacy.sh"
CARGO = APP / "rust-core" / "Cargo.toml"
VERSION = "3.0.3"

text = RUN.read_text(encoding="utf-8")

# Release/runtime version parity. release_prepare.py updates the other public surfaces,
# while run_legacy.sh and the native crate are intentionally handled here.
text = re.sub(r'(?m)^APP_VERSION="[^"]+"$', f'APP_VERSION="{VERSION}"', text, count=1)
text = re.sub(r'(?m)^REQUIRED_PACKAGE_VERSION="[^"]+"$', f'REQUIRED_PACKAGE_VERSION="{VERSION}"', text, count=1)

# Logging cadence constants. These affect only human-readable log emission; the controller,
# AI evaluator, status JSON and telemetry keep their existing 10 s/5 s execution cadence.
anchor = 'AI_RUNTIME_RELAY_KEEPALIVE_SECONDS=300\n'
insert = (
    'AI_RUNTIME_RELAY_KEEPALIVE_SECONDS=300\n'
    'ADAPTIVE_PWM_LOG_KEEPALIVE_WRITES=6\n'
    'AI_COOLING_LOG_KEEPALIVE_CYCLES=30\n'
)
if anchor not in text:
    raise SystemExit('logging constants anchor not found')
text = text.replace(anchor, insert, 1)

# Add a lightweight write-log counter to the controller-local state.
old_local = 'local low_count=0 up_count=0 up_hold=0 deadband_count=0 controller_state=-1 base_state=-1 action="hold" writable=false last_logged="" safety_delta=10000 fast_delta=6000'
new_local = 'local low_count=0 up_count=0 up_hold=0 deadband_count=0 controller_state=-1 base_state=-1 action="hold" writable=false last_logged="" adaptive_write_log_tick=0 adaptive_log_important=false safety_delta=10000 fast_delta=6000'
if old_local not in text:
    raise SystemExit('adaptive local-state anchor not found')
text = text.replace(old_local, new_local, 1)

# Reset the sampling counter on configuration hot reload so diagnostics remain intuitive.
old_reset = 'controller_state=-1; base_state=-1; adaptive_trim=0; low_count=0; up_count=0; up_hold=0; deadband_count=0; last_logged=""'
new_reset = 'controller_state=-1; base_state=-1; adaptive_trim=0; low_count=0; up_count=0; up_hold=0; deadband_count=0; last_logged=""; adaptive_write_log_tick=0'
if old_reset not in text:
    raise SystemExit('adaptive reload reset anchor not found')
text = text.replace(old_reset, new_reset, 1)

# AI log key no longer includes the rapidly alternating model_agrees/model_nudge reason.
# State/bucket/confidence/prediction/qualified-count changes still log immediately, while
# steady state gets a five-minute keepalive (30 evaluator cycles at 10 s).
old_ai = '''          elif { [ "$ai_last_log" != "${ai_state}:${ai_reason}:${ai_bucket}:${ai_conf}:${ai_prediction}:${ai_qualified_samples}" ] || [ $((ai_log_tick % 6)) -eq 0 ]; } && { [ "$ai_state" = "assist" ] || [ "$ai_reason" = "insufficient_qualified_samples" ] || [ "$ai_bin_observations" = "1" ]; }; then
            log "AI Cooling: state=${ai_state}; reason=${ai_reason}; bucket=${ai_bucket}; observations=${ai_bin_observations}; qualified=${ai_qualified_samples}/${AI_COOLING_MIN_SAMPLES}; confidence=${ai_conf}%; prediction=${ai_prediction}%; qualification=${ai_qualification_reason}."
            ai_last_log="${ai_state}:${ai_reason}:${ai_bucket}:${ai_conf}:${ai_prediction}:${ai_qualified_samples}"
          fi
'''
new_ai = '''          elif { [ "$ai_last_log" != "${ai_state}:${ai_bucket}:${ai_conf}:${ai_prediction}:${ai_qualified_samples}" ] || [ $((ai_log_tick % AI_COOLING_LOG_KEEPALIVE_CYCLES)) -eq 0 ]; } && { [ "$ai_state" = "assist" ] || [ "$ai_reason" = "insufficient_qualified_samples" ] || [ "$ai_bin_observations" = "1" ]; }; then
            log "AI Cooling: state=${ai_state}; reason=${ai_reason}; bucket=${ai_bucket}; observations=${ai_bin_observations}; qualified=${ai_qualified_samples}/${AI_COOLING_MIN_SAMPLES}; confidence=${ai_conf}%; prediction=${ai_prediction}%; qualification=${ai_qualification_reason}."
            ai_last_log="${ai_state}:${ai_bucket}:${ai_conf}:${ai_prediction}:${ai_qualified_samples}"
          fi
'''
if old_ai not in text:
    raise SystemExit('AI logging anchor not found')
text = text.replace(old_ai, new_ai, 1)

# Successful controller writes remain fully executed and reflected in status telemetry.
# Human-readable logs are sampled to roughly one per six actual writes (~60 s under active
# regulation), except safety-relevant fast/sign-guard/reassert actions which log immediately.
old_pwm = '''          if [ "$last_logged" != "$action:$current:$desired" ]; then
            log "Adaptive PWM: T=$(millideg_to_c_1dp "$temp_milli")°C target=${CURVE1_TARGET_C}°C curve=${curve_state}% trim=${adaptive_trim}pp controller ${current}->${desired}/${max_state} (${action}); owner=adaptive."
            last_logged="$action:$current:$desired"
          fi
'''
new_pwm = '''          adaptive_write_log_tick=$((adaptive_write_log_tick + 1))
          adaptive_log_important=false
          case "$action" in
            *fast*|*sign_guard*|reassert_owner_state) adaptive_log_important=true ;;
          esac
          if [ "$last_logged" != "$action:$current:$desired" ]; then
            if [ "$adaptive_log_important" = "true" ] || [ "$adaptive_write_log_tick" -eq 1 ] || [ $((adaptive_write_log_tick % ADAPTIVE_PWM_LOG_KEEPALIVE_WRITES)) -eq 0 ]; then
              log "Adaptive PWM: T=$(millideg_to_c_1dp "$temp_milli")°C target=${CURVE1_TARGET_C}°C curve=${curve_state}% trim=${adaptive_trim}pp controller ${current}->${desired}/${max_state} (${action}); owner=adaptive."
            fi
            last_logged="$action:$current:$desired"
          fi
'''
if old_pwm not in text:
    raise SystemExit('Adaptive PWM logging anchor not found')
text = text.replace(old_pwm, new_pwm, 1)

# Make the effective log policy visible at startup without changing execution intervals.
old_perf = 'boot-cache=${BOOT_CONFIG_CACHE_SECONDS}s; AI evaluator=$((AI_COOLING_EVAL_CYCLES * ADAPTIVE_PWM_INTERVAL_SECONDS))s.'
new_perf = 'boot-cache=${BOOT_CONFIG_CACHE_SECONDS}s; AI evaluator=$((AI_COOLING_EVAL_CYCLES * ADAPTIVE_PWM_INTERVAL_SECONDS))s; control-log=sample/${ADAPTIVE_PWM_LOG_KEEPALIVE_WRITES} writes; AI-log-keepalive=$((AI_COOLING_LOG_KEEPALIVE_CYCLES * ADAPTIVE_PWM_INTERVAL_SECONDS))s.'
if old_perf not in text:
    raise SystemExit('performance startup-log anchor not found')
text = text.replace(old_perf, new_perf, 1)

RUN.write_text(text, encoding="utf-8")

cargo = CARGO.read_text(encoding="utf-8")
cargo, n = re.subn(r'(?m)^version = "[^"]+"$', f'version = "{VERSION}"', cargo, count=1)
if n != 1:
    raise SystemExit('Cargo package version anchor not found')
CARGO.write_text(cargo, encoding="utf-8")

print('Prepared SBC5 3.0.3 log/I-O optimization anchors')
