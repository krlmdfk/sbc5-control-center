#!/usr/bin/env python3
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def replace_once(path, old, new):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'missing anchor in {path}: {old[:80]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')

# README — current capabilities, EN/PL, no version-history prose.
p = ROOT / 'README.md'
text = p.read_text(encoding='utf-8')
text = re.sub(r'<strong>Stable · v[^·]+ · Card UI [^·]+ · aarch64', '<strong>Stable · v3.1.6 · Card UI 3.1.6 · aarch64', text, count=1)
text = text.replace('| **AI Cooling** | local Learning/Assist, workload buckets, sample qualification, prediction history |',
                    '| **AI Cooling + Thermal Predictor** | local Learning/Assist, workload buckets, qualified samples, +30/+60/+120 s forecasts, Predictor quality/MAE, Shadow Assist |', 1)
text = text.replace('| **AI Cooling** | lokalny Learning/Assist, buckety obciążenia, kwalifikacja próbek, historia predykcji |',
                    '| **AI Cooling + Thermal Predictor** | lokalny Learning/Assist, buckety obciążenia, próbki jakościowe, prognozy +30/+60/+120 s, jakość/MAE Predictora, Shadow Assist |', 1)
eng_anchor = '### CPU, GPU and `config.txt`\n'
eng_section = '''### AI Thermal Predictor v2\n\nAI Thermal Predictor forecasts CPU temperature at **+30 s, +60 s and +120 s**. The current v2 algorithm is closed-loop aware: it combines the measured temperature trend with horizon-specific anchoring toward the configured thermal target and a bounded online bias correction learned separately for each horizon. Quality is measured with MAE, confidence, validated samples and per-horizon error telemetry.\n\n**Shadow Assist** evaluates a bounded future PWM correction (currently up to ±2 percentage points) but remains non-authoritative: `control_output_enabled=false`, so Adaptive PWM and AI Cooling remain the only physical control path. The activation gate requires `good`/`excellent` Predictor quality, confidence ≥80%, average MAE ≤1.25 °C and sufficient validated samples for every horizon.\n\n'''
if '### AI Thermal Predictor v2' not in text:
    text = text.replace(eng_anchor, eng_section + eng_anchor, 1)
pl_anchor = '### CPU, GPU i `config.txt`\n'
pl_section = '''### AI Thermal Predictor v2\n\nAI Thermal Predictor prognozuje temperaturę CPU dla **+30 s, +60 s i +120 s**. Algorytm v2 uwzględnia zamkniętą pętlę chłodzenia: łączy zmierzony trend temperatury z zależnym od horyzontu powrotem w stronę ustawionego celu termicznego oraz ograniczoną korektą błędu uczoną osobno dla każdego horyzontu. Jakość jest mierzona przez MAE, confidence, liczbę zweryfikowanych prognoz i błędy poszczególnych horyzontów.\n\n**Shadow Assist** wylicza ograniczoną przyszłą korektę PWM (obecnie do ±2 pp), ale pozostaje nieautorytatywny: `control_output_enabled=false`, więc jedyną fizyczną ścieżką sterowania pozostają Adaptive PWM i AI Cooling. Bramka aktywacji wymaga jakości `good`/`excellent`, confidence ≥80%, średniego MAE ≤1,25 °C i odpowiedniej liczby walidacji dla każdego horyzontu.\n\n'''
if text.count('### AI Thermal Predictor v2') < 2:
    text = text.replace(pl_anchor, pl_section + pl_anchor, 1)
p.write_text(text, encoding='utf-8')

# INFO — current-state overview only.
p = ROOT / 'INFO.md'
text = p.read_text(encoding='utf-8')
text = re.sub(r'\| App version / Wersja aplikacji \| \*\*[^*]+\*\* \|', '| App version / Wersja aplikacji | **3.1.6** |', text, count=1)
text = re.sub(r'\| Card UI \| \*\*[^*]+\*\* \|', '| Card UI | **3.1.6** |', text, count=1)
en = 'AI Cooling runs locally and is secondary to the classical controller. The model distinguishes `idle`, `low`, `medium` and `high` workload buckets, qualifies samples and can operate in a limited Assist mode.\n'
en_add = en + '\nAI Thermal Predictor v2 forecasts CPU temperature 30/60/120 seconds ahead and scores itself using per-horizon MAE, signed online bias, confidence and validated-sample maturity. Shadow Assist converts that forecast into a bounded hypothetical PWM delta while remaining telemetry-only (`control_output_enabled=false`); Adaptive PWM and AI Cooling remain authoritative. Predictor v1 quality statistics are archived when v2 starts so old errors do not contaminate the new model, while the AI Cooling model and counters are preserved.\n'
if 'Predictor v1 quality statistics are archived' not in text:
    text = text.replace(en, en_add, 1)
pl = 'AI Cooling działa lokalnie i wtórnie wobec klasycznego regulatora. Model rozróżnia buckety `idle`, `low`, `medium` i `high`, kwalifikuje próbki jakościowe oraz może pracować w ograniczonym trybie Assist.\n'
pl_add = pl + '\nAI Thermal Predictor v2 prognozuje temperaturę CPU z wyprzedzeniem 30/60/120 sekund i ocenia się przez MAE dla horyzontów, znakowaną korektę błędu online, confidence oraz dojrzałość zweryfikowanych próbek. Shadow Assist zamienia prognozę na ograniczoną hipotetyczną korektę PWM, ale pozostaje wyłącznie telemetryczny (`control_output_enabled=false`); Adaptive PWM i AI Cooling pozostają nadrzędne. Przy starcie v2 statystyki jakości Predictora v1 są archiwizowane, aby stare błędy nie zafałszowały nowego modelu, natomiast model i liczniki AI Cooling są zachowane.\n'
if 'statystyki jakości Predictora v1 są archiwizowane' not in text:
    text = text.replace(pl, pl_add, 1)
p.write_text(text, encoding='utf-8')

# Documentation — usage/architecture only, no changelog wording.
p = ROOT / 'DOCUMENTATION.md'
text = p.read_text(encoding='utf-8')
marker = '## AI Thermal Predictor v2 / Predyktor termiczny AI v2'
if marker not in text:
    text += '''\n\n---\n\n## AI Thermal Predictor v2 / Predyktor termiczny AI v2\n\n**EN.** Thermal Predictor is an observe-only forecasting layer fed by the existing AI runtime window; it adds no separate fast polling loop. Forecasts are published for +30, +60 and +120 seconds. Version 2 uses the measured temperature slope, horizon-specific target anchoring and a bounded signed bias correction learned online per horizon. Use `Average MAE`, `MAE 30s/60s/120s`, `Last Error`, `Confidence`, `Quality`, `Validated Samples` and `Data Age` to judge readiness.\n\nShadow Assist exposes the recommendation that a future predictive controller would make. The recommendation is limited to ±2 percentage points and is gated by Predictor quality. In the current operating mode it never writes physical PWM: `control_output_enabled=false`. The existing Adaptive PWM slew limiter, Sign Guard, AI Cooling and emergency safety behavior remain unchanged.\n\n**PL.** Thermal Predictor jest warstwą prognozującą pracującą w trybie obserwacyjnym i korzysta z istniejącego okna AI runtime; nie dodaje osobnej szybkiej pętli odpytywania. Publikuje prognozy +30, +60 i +120 sekund. Wersja 2 wykorzystuje zmierzony trend temperatury, zależne od horyzontu dociąganie prognozy do celu termicznego oraz ograniczoną znakowaną korektę błędu uczoną online osobno dla każdego horyzontu. Gotowość ocenia się przez `Average MAE`, `MAE 30s/60s/120s`, `Last Error`, `Confidence`, `Quality`, `Validated Samples` i `Data Age`.\n\nShadow Assist pokazuje rekomendację, którą w przyszłości mógłby wykonać regulator predykcyjny. Rekomendacja jest ograniczona do ±2 punktów procentowych i przechodzi bramkę jakości Predictora. W obecnym trybie nigdy nie zapisuje fizycznego PWM: `control_output_enabled=false`. Istniejące zabezpieczenia Adaptive PWM, slew limiter, Sign Guard, AI Cooling i tryb awaryjny pozostają bez zmian.\n'''
p.write_text(text, encoding='utf-8')

# Focused AI documentation / website.
for rel in ('docs/ai-cooling.md', 'docs/index.md'):
    p = ROOT / rel
    text = p.read_text(encoding='utf-8')
    marker = '## AI Thermal Predictor v2'
    if marker not in text:
        text += '''\n\n## AI Thermal Predictor v2\n\nSBC5 includes a closed-loop-aware Thermal Predictor for +30/+60/+120 second CPU temperature forecasts. Predictor v2 combines trend extrapolation with target anchoring and bounded online bias correction. Its quality gate uses MAE, confidence and validated samples. Shadow Assist is telemetry-only and evaluates a bounded ±2 pp PWM recommendation without changing physical fan output.\n\nThe Predictor uses the existing AI runtime cadence; no additional fast polling loop is created.\n'''
    p.write_text(text, encoding='utf-8')

# Prepare the professional bilingual release and rebuild all hashes.
cmd = [
    'python', 'scripts/release_prepare.py',
    '--version', '3.1.6',
    '--restart-required', 'none',
    '--summary-en', 'Improve AI Thermal Predictor accuracy with closed-loop target anchoring and online per-horizon bias calibration while keeping Shadow Assist observe-only.',
    '--summary-pl', 'Poprawa dokładności AI Thermal Predictor przez uwzględnienie zamkniętej pętli, dociąganie do celu termicznego i korektę błędu online dla każdego horyzontu przy zachowaniu Shadow Assist bez wpływu na PWM.',
    '--changed-en', 'Thermal Predictor v2 uses horizon-specific target anchoring and bounded signed online bias calibration for +30/+60/+120 s forecasts.',
    '--changed-pl', 'Thermal Predictor v2 wykorzystuje zależne od horyzontu dociąganie do celu i ograniczoną znakowaną korektę błędu online dla prognoz +30/+60/+120 s.',
    '--changed-en', 'Shadow Assist remains telemetry-only with control_output_enabled=false and the existing ±2 pp recommendation limit.',
    '--changed-pl', 'Shadow Assist pozostaje wyłącznie telemetryczny z control_output_enabled=false i dotychczasowym limitem rekomendacji ±2 pp.',
    '--fixed-en', 'Archive Predictor v1 quality statistics when migrating to v2 so historical errors cannot distort the new accuracy gate.',
    '--fixed-pl', 'Archiwizacja statystyk jakości Predictora v1 podczas migracji do v2, aby historyczne błędy nie zafałszowały nowej bramki jakości.',
    '--performance-en', 'Reuse the existing AI runtime cadence; no new fast polling loop or physical PWM write path is added.',
    '--performance-pl', 'Wykorzystanie istniejącego cyklu AI runtime bez nowej szybkiej pętli odpytywania i bez nowej ścieżki zapisu fizycznego PWM.',
]
subprocess.run(cmd, cwd=ROOT, check=True)
print('Prepared SBC5 3.1.6 code/docs/release candidate')

# trigger-only touch
