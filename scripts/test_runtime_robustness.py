#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'local_apps/sbc5_control_center'
bootstrap = (APP / 'run.sh').read_text(encoding='utf-8')
legacy = (APP / 'run_legacy.sh').read_text(encoding='utf-8')
docker = (APP / 'Dockerfile').read_text(encoding='utf-8')
yaml_card = (ROOT / 'dashboard/sbc5_control_center_diagnostics_card.yaml').read_text(encoding='utf-8')
card = json.loads((APP / 'dashboard_card.json').read_text(encoding='utf-8'))
builder = (ROOT / 'scripts/build_local_update.py').read_text(encoding='utf-8')
release = (ROOT / 'scripts/release_easy.py').read_text(encoding='utf-8')
workflow = (ROOT / '.github/workflows/validate.yml').read_text(encoding='utf-8')
auto_release = (ROOT / '.github/workflows/auto-release.yml').read_text(encoding='utf-8')

# 3.0.0 splits startup into a minimal Rust bootstrap and the proven compatibility
# control plane. Runtime safety assertions must follow the code that owns them.
assert 'mkdir -p /tmp' in bootstrap
assert 'install -d -m 1777 /tmp' in docker
assert 'sbc5-core' in bootstrap
assert 'self-test' in bootstrap
assert 'SBC5_RUST_CORE_ENABLED=true' in bootstrap
assert 'SBC5_RUST_CORE_ENABLED=false' in bootstrap
assert 'exec /run_legacy.sh' in bootstrap
assert 'COPY run_legacy.sh ' in docker
assert 'chmod a+x /run.sh /run_legacy.sh' in docker

# 3.1.18 Ethernet state persistence regression.
guard = (APP / 'ethernet_guard.py').read_text(encoding='utf-8')
config_ui = (APP / 'config_ui.py').read_text(encoding='utf-8')
assert 'SETTINGS_PATH = Path("/data/ethernet_settings.json")' in guard
assert 'persistent = read_persistent_settings()' in guard
assert 'eee_status = "off_active"' in guard
assert 'eee_status = "auto_pending_restart"' in guard
assert "ETHERNET_STATE = Path('/data/ethernet_settings.json')" in config_ui
assert "persist_ethernet_state(o,source='config_ui',explicit=True)" in config_ui
assert 'tee -a /tmp/sbc5_ethernet_guard.log' in bootstrap

# Host-access warning throttling and Supervisor diagnostics remain authoritative
# in the compatibility control plane during the stable 3.0.0 migration.
assert 'boot_access_warn_throttled' in legacy
assert 'Host Access Guard: Supervisor protected=' in legacy

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
