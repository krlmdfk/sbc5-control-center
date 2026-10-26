#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
run = (ROOT / 'local_apps/sbc5_control_center/run.sh').read_text(encoding='utf-8')
docker = (ROOT / 'local_apps/sbc5_control_center/Dockerfile').read_text(encoding='utf-8')
yaml_card = (ROOT / 'dashboard/sbc5_control_center_diagnostics_card.yaml').read_text(encoding='utf-8')
card = json.loads((ROOT / 'local_apps/sbc5_control_center/dashboard_card.json').read_text(encoding='utf-8'))
builder = (ROOT / 'scripts/build_local_update.py').read_text(encoding='utf-8')
release = (ROOT / 'scripts/release_easy.py').read_text(encoding='utf-8')
workflow = (ROOT / '.github/workflows/validate.yml').read_text(encoding='utf-8')
auto_release = (ROOT / '.github/workflows/auto-release.yml').read_text(encoding='utf-8')

assert 'mkdir -p /tmp' in run and 'chmod 1777 /tmp' in run
assert 'install -d -m 1777 /tmp' in docker
assert 'boot_access_warn_throttled' in run
assert 'Host Access Guard: Supervisor protected=' in run
assert 'ai.qualification_limits.temperature_window_min_points' not in yaml_card
card_raw = json.dumps(card, ensure_ascii=False)
assert 'ai.qualification_limits.temperature_window_min_points' not in card_raw
assert 'limits.temperature_window_min_points' in yaml_card
assert 'limits.temperature_window_min_points' in card_raw
assert 'tempfile.gettempdir()' in builder
assert 'tempfile.gettempdir()' in release

# Normal CI validates repository/runtime consistency but must not rebuild or
# mutate an already-published release artifact after documentation-only commits.
assert 'test_runtime_robustness.py' in workflow
assert 'python scripts/validate_release.py' in workflow
assert '$RUNNER_TEMP/SBC5_UPDATE_CI.zip' not in workflow

# Release publication remains strict and reproducible.
assert 'build_local_update.py' in auto_release
assert '--strict-manifest-hashes' in auto_release
assert 'gh release create' in auto_release
assert 'gh release view' in auto_release
assert 'exists=true' in auto_release
assert '--clobber' not in auto_release

print('Runtime robustness regression PASS')
