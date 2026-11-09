#!/usr/bin/env python3
"""Subprocess-restart regression for the complete SBC5 v5.2 AI learning stack.

Each evaluator invocation is a new Python process, corresponding to distinct
App control-loop executions; a preserved /data model must not reset counters.
This is not a substitute for a real HAOS/App restart or installation test.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
EVALUATOR = APP / "ai_cooling_v5_2.py"


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def evaluate(model: Path, status: Path, mirror: Path, telemetry: Path, grid: Path):
    command = [
        sys.executable, str(EVALUATOR), "step",
        "--model", str(model), "--status", str(status),
        "--mirror", str(mirror), "--telemetry", str(telemetry),
        "--require-private-telemetry",
        "--mode", "learning", "--control-mode", "hybrid",
        "--controller-action", "hold",
        "--temp-milli", "49000", "--target", "49.0",
        "--pwm", "43", "--baseline", "43",
        "--min-safe", "10", "--maximum", "100",
        "--assist-limit", "4", "--deadband", "0.75",
        "--min-samples", "30", "--grid-profile", str(grid),
    ]
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=15, check=False
    )
    assert result.returncode == 0, (
        f"AI evaluator process failed: {result.returncode}\n"
        f"stdout={result.stdout[-2500:]}\nstderr={result.stderr[-2500:]}"
    )
    assert result.stdout.strip(), "AI evaluator did not return a control result"
    assert model.is_file() and status.is_file() and mirror.is_file()
    return load(model), load(status)


def main():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        model = root / "ai_cooling_model.json"
        status = root / "ai_cooling_status.json"
        mirror = root / "ai_cooling_mirror.json"
        telemetry = root / "private_telemetry.json"
        grid = root / "grid.json"

        # Snapshot shaped like the trained low-workload state; use existing
        # regression fields and retain qualified EMA/history.
        seed = {
            "schema": 5,
            "created_epoch": int(time.time()) - 86400,
            "observations_total": 40072,
            "qualified_samples_total": 1169,
            "legacy_samples_total": 0,
            "bins": {
                "49.0|low": {
                    "observations": 40072,
                    "qualified_n": 1169,
                    "ema_pwm": 43.0,
                    "ema_dev": 1.1,
                    "last_qualified_cpu_load_percent": 12.0,
                    "last_cpu_load_percent": 12.0,
                    "last_pwm_percent": 43,
                    "last_temp_c": 49.0,
                },
            },
            "temperature_density": {},
            "workload_load_history": [],
            "last_training_sample_epoch": time.time(),
        }
        model.write_text(json.dumps(seed, ensure_ascii=False), encoding="utf-8")
        telemetry.write_text(json.dumps({
            "schema": 1,
            "sample_epoch": int(time.time()),
            "cpu_core_usage_percent": [10.0, 12.0, 11.0, 15.0],
            "load_1m": 0.36,
            "cpu_core_count": 4,
            "pmic_power_w": 5.5,
            "cpu_frequency_mhz": 2500,
        }), encoding="utf-8")
        telemetry.chmod(0o600)

        initial = hashlib.sha256(model.read_bytes()).hexdigest()
        first, first_status = evaluate(model, status, mirror, telemetry, grid)
        assert first["observations_total"] == seed["observations_total"]
        assert first["qualified_samples_total"] == seed["qualified_samples_total"]
        assert first["bins"]["49.0|low"]["qualified_n"] == 1169
        assert first["bins"]["49.0|low"]["ema_pwm"] == 43.0
        assert hashlib.sha256(model.read_bytes()).hexdigest() != initial
        assert first_status["observations_total"] == 40072

        # A new interpreter must read the state created by the previous process.
        second, second_status = evaluate(model, status, mirror, telemetry, grid)
        assert second["observations_total"] == 40072
        assert second["qualified_samples_total"] == 1169
        assert second["bins"]["49.0|low"]["qualified_n"] == 1169
        assert second["bins"]["49.0|low"]["ema_pwm"] == 43.0
        assert second_status["observations_total"] == 40072
        assert second_status["qualified_samples_total"] == 1169
        assert "hierarchical_v5" in second, "v5 learning state was not retained"

        # No reset or migration ran: the model persisted solely across process
        # shutdown/startup, as it should on the same /data filesystem.
        print("AI v5.2 full-process restart model persistence: PASS")


if __name__ == "__main__":
    main()
