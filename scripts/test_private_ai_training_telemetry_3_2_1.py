#!/usr/bin/env python3
"""Private training telemetry cannot be substituted with HA config telemetry."""
from __future__ import annotations

from pathlib import Path
import importlib.util
import json
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps/sbc5_control_center"
RUN = (APP / "run_legacy.sh").read_text(encoding="utf-8")
AI = APP / "ai_cooling_legacy.py"
spec = importlib.util.spec_from_file_location("sbc5_private_telemetry", AI)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def valid_snapshot(now: int) -> dict:
    return {
        "schema": 1, "sample_epoch": now,
        "cpu_core_usage_percent": [8.0, 10.0, 12.0, 6.0],
        "load_1m": 0.36, "cpu_core_count": 4,
        "pmic_power_w": 5.5, "cpu_frequency_mhz": 2500,
    }


with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "training.json"

    def write(data, perms=0o600):
        path.write_text(json.dumps(data), encoding="utf-8")
        path.chmod(perms)

    now = int(time.time())
    good = valid_snapshot(now)
    write(good)
    assert mod._private_telemetry(path, now + 1) == good
    assert mod._cpu_load(good) == 9.0

    path.chmod(0o644)
    assert mod._private_telemetry(path, now) is None
    path.chmod(0o600)

    for field, bad in [
        ("schema", 999),
        ("sample_epoch", now - 100),
        ("sample_epoch", now + 100),
        ("cpu_core_usage_percent", []),
        ("cpu_core_usage_percent", [50, 200]),
        ("cpu_core_usage_percent", [float("nan")]),
        ("cpu_core_count", 0),
        ("load_1m", float("inf")),
        ("pmic_power_w", -1),
        ("cpu_frequency_mhz", 1e7),
    ]:
        corrupted = {**good, field: bad}
        write(corrupted)
        assert mod._private_telemetry(path, now) is None, f"accepted invalid {field}={bad!r}"

    write(good)
    path.write_text("not-json")
    assert mod._private_telemetry(path, now) is None

    path.unlink()
    path.symlink_to(Path(tmp) / "not-present")
    assert mod._private_telemetry(path, now) is None
    path.unlink()

    path.write_bytes(b"X" * (mod.PRIVATE_TELEMETRY_MAX_SIZE_BYTES + 1))
    path.chmod(0o600)
    assert mod._private_telemetry(path, now) is None

assert 'AI_TRAINING_TELEMETRY_FILE="/data/ai_training_telemetry.json"' in RUN
assert 'TELEMETRY_STATE_FILE="/homeassistant/sbc5_control_center/telemetry.json"' in RUN
assert '--telemetry "$AI_TRAINING_TELEMETRY_FILE" --require-private-telemetry' in RUN
assert 'mktemp "\${AI_TRAINING_TELEMETRY_FILE}.XXXXXX"' in RUN
assert 'mv -f -- "$ai_training_tmp" "$AI_TRAINING_TELEMETRY_FILE"' in RUN
assert 'AI_TRAINING_TELEMETRY_FILE' not in (APP / "config_ui.py").read_text(encoding="utf-8")
legacy = AI.read_text(encoding="utf-8")
assert 'if args.require_private_telemetry:' in legacy
assert 'if telemetry is None:' in legacy
assert 'return 2' in legacy

print("SBC5 private AI training telemetry validation: PASS")
