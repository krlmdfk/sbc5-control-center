#!/usr/bin/env python3
from pathlib import Path

path = Path("local_apps/sbc5_control_center/run_legacy.sh")
text = path.read_text(encoding="utf-8")

old_decl = 'ai_effective_prediction=-1 ai_transfer_source="legacy" ai_effective_coverage=0'
new_decl = old_decl + ' tp_mode="" tp_f30="" tp_f60="" tp_f120="" tp_conf=0 tp_mae="" tp_weighted="" tp_error="" tp_gain="" tp_weights="" tp_accepted=0 tp_rejected=0'
if new_decl not in text:
    if old_decl not in text:
        raise SystemExit("AI declaration anchor not found")
    text = text.replace(old_decl, new_decl, 1)

old_read = 'ai_effective_prediction ai_transfer_source ai_effective_coverage <<< "$ai_result"'
new_read = 'ai_effective_prediction ai_transfer_source ai_effective_coverage tp_mode tp_f30 tp_f60 tp_f120 tp_conf tp_mae tp_weighted tp_error tp_gain tp_weights tp_accepted tp_rejected <<< "$ai_result"'
if new_read not in text:
    if old_read not in text:
        raise SystemExit("AI TSV read anchor not found")
    text = text.replace(old_read, new_read, 1)

anchor = '            ai_last_log="${ai_state}:${ai_bucket}:${ai_conf}:${ai_prediction}:${ai_qualified_samples}:${ai_effective_conf}:${ai_transfer_source}:${ai_effective_coverage}"\n'
log_line = '            log "Thermal Predictor: mode=${tp_mode}; F30=${tp_f30}C F60=${tp_f60}C F120=${tp_f120}C; confidence=${tp_conf}%; MAE_avg=${tp_mae}C; weighted=${tp_weighted}C error=${tp_error}C; weights=${tp_weights}; gain=${tp_gain}; accepted/rejected=${tp_accepted}/${tp_rejected}; AI_delta=${ai_correction}pp; guard=${ai_reason}."\n'
log_block = anchor + '''          fi
          # 3.1.21 Thermal Predictor observability travels in the existing AI evaluator TSV.
          # Log every ~60 s to keep diagnostics useful without adding polling or log spam.
          if [ -n "${tp_mode:-}" ] && [ $((ai_log_tick % 6)) -eq 0 ]; then
''' + log_line + '          fi\n'
marker = 'Thermal Predictor: mode=${tp_mode};'
if marker not in text:
    if anchor not in text:
        raise SystemExit("AI log insertion anchor not found")
    text = text.replace(anchor + '          fi\n', log_block, 1)
else:
    # Repair the first 3.1.21 patch which omitted the closing `fi` for the
    # diagnostics guard. Insert it immediately after the unique log line.
    broken = log_line + '        fi\n      fi\n'
    fixed = log_line + '          fi\n        fi\n      fi\n'
    if broken in text:
        text = text.replace(broken, fixed, 1)

path.write_text(text, encoding="utf-8")
print("Thermal Predictor log patch 3.1.21 applied")
