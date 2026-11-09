#!/usr/bin/env python3
"""Regression: reset must wait for a complete AI v5.2 learning transaction."""
from __future__ import annotations

import json
import multiprocessing
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
sys.path.insert(0, str(APP))

from ai_model_lock import ai_model_lock
from config_ui import reset_ai_model_with_backup


def evaluator(model: str, lock: str, acquired, release, errors):
    try:
        import ai_cooling_v5_2
        def simulate_full_step():
            acquired.set()
            if not release.wait(8):
                raise TimeoutError("Evaluator release was not signaled")
            Path(model).write_text(json.dumps({
                "schema": 5, "observations_total": 40073,
                "qualified_samples_total": 1170,
            }), encoding="utf-8")
            return 0
        # The production entrypoint must lock the ENTIRE nested v4-v5.2 step.
        ai_cooling_v5_2.base.main = simulate_full_step
        # Point the shared model lock at an isolated test file.
        import ai_model_lock
        ai_model_lock.AI_MODEL_LOCK_PATH = Path(lock)
        sys.argv = ["ai_cooling.py", "step"]
        assert ai_cooling_v5_2.main() == 0
    except Exception as exc:
        errors.put(f"evaluator: {exc!r}")


def resetter(model: str, backups: str, status: str, mirror: str,
             lock: str, started, finished, results):
    try:
        started.set()
        snapshot = reset_ai_model_with_backup(
            model_path=Path(model), backup_dir=Path(backups),
            status_path=Path(status), mirror_path=Path(mirror),
            lock_path=Path(lock),
        )
        results.put(snapshot)
    except Exception as exc:
        results.put({"error": repr(exc)})
    finally:
        finished.set()


def run():
    # Linux-based GitHub runner / HAOS; FLOCK is cross-process.
    ctx = multiprocessing.get_context("fork")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        model = root / "ai_cooling_model.json"
        lock = root / "ai_cooling_model.lock"
        backups = root / "backups"
        status = root / "status.json"
        mirror = root / "mirror.json"
        model.write_text(json.dumps({
            "schema": 5, "observations_total": 40072,
            "qualified_samples_total": 1169,
        }), encoding="utf-8")
        status.write_text('{"state":"assist"}', encoding="utf-8")
        mirror.write_text('{"state":"assist"}', encoding="utf-8")

        acquired, release = ctx.Event(), ctx.Event()
        started, finished = ctx.Event(), ctx.Event()
        errors, results = ctx.Queue(), ctx.Queue()
        learner = ctx.Process(
            target=evaluator, args=(str(model), str(lock), acquired, release, errors)
        )
        reset = ctx.Process(
            target=resetter,
            args=(str(model), str(backups), str(status), str(mirror),
                  str(lock), started, finished, results),
        )
        learner.start()
        assert acquired.wait(5), "AI evaluator did not enter the locked transaction"
        reset.start()
        assert started.wait(5), "Reset did not start"
        try:
            # The reset must not delete files while the evaluator holds FLOCK.
            assert not finished.wait(0.35), "Reset raced the active evaluator"
            assert model.exists(), "AI model removed while evaluator held lock"
        finally:
            release.set()
            learner.join(timeout=8)
            reset.join(timeout=8)
            if learner.is_alive():
                learner.terminate()
                learner.join()
                raise AssertionError("AI evaluator deadlocked")
            if reset.is_alive():
                reset.terminate()
                reset.join()
                raise AssertionError("AI reset deadlocked")

        assert learner.exitcode == 0, learner.exitcode
        assert reset.exitcode == 0, reset.exitcode
        assert errors.empty(), errors.get() if not errors.empty() else None
        snapshot = results.get(timeout=1)
        assert "error" not in snapshot, snapshot
        backup = Path(snapshot["backup"])
        restored = json.loads(backup.read_text(encoding="utf-8"))
        assert restored["observations_total"] == 40073, restored
        assert restored["qualified_samples_total"] == 1170, restored
        assert not model.exists(), "Pre-reset state was resurrected"
        assert not status.exists() and not mirror.exists()
        assert lock.exists(), "The shared lock inode must persist after reset"

        # A held lock rejects other writers rather than silently bypassing it.
        with ai_model_lock(lock_path=lock, timeout_seconds=1.0):
            try:
                with ai_model_lock(lock_path=lock, timeout_seconds=0.15):
                    raise AssertionError("Lock was simultaneously acquired twice")
            except TimeoutError:
                pass

        # Post-reset new learning may start from a genuine empty state normally.
        with ai_model_lock(lock_path=lock, timeout_seconds=1.0):
            model.write_text(json.dumps({"schema": 5, "observations_total": 1}),
                             encoding="utf-8")
        assert json.loads(model.read_text())["observations_total"] == 1

    print("AI model concurrent reset / learning transaction: PASS")


if __name__ == "__main__":
    run()
