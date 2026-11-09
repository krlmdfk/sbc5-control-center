#!/usr/bin/env python3
"""AI diagnosis must inspect copies without mutating active state."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "local_apps/sbc5_control_center/ai_model_diagnostics.py"
spec = importlib.util.spec_from_file_location("sbc5_diagnostics_test", SOURCE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    model = root / "ai_cooling_model.json"
    backups = root / "backups"
    migration = root / "migration_backups"
    legacy = root / "data_export" / "ai_cooling_model.json"
    backups.mkdir()
    backup = backups / "ai_cooling_model_20261109_123000_a.json"
    state = {
        "schema": 5, "observations_total": 40072,
        "qualified_samples_total": 1169,
        "hierarchical_v5": {"targets": {"50": {"private_training": [1, 2, 3]}}},
        "legacy_workload_v1": {"observations_total": 1245, "qualified_samples_total": 31},
    }
    model.write_text(json.dumps(state), encoding="utf-8")
    backup.write_bytes(model.read_bytes())
    digest = hashlib.sha256(model.read_bytes()).hexdigest()
    before = {p: p.read_bytes() for p in (model, backup)}

    output = mod.inventory(model, backups, migration, legacy)
    active = output["active_model"]
    assert active["observations_total"] == 40072
    assert active["qualified_samples_total"] == 1169
    assert active["legacy_observations_total"] == 1245
    assert active["sha256"] == digest
    assert active["has_hierarchical_v5"] is True
    assert len(output["candidate_backups"]) == 1
    assert "private_training" not in json.dumps(output)
    assert all(path.read_bytes() == raw for path, raw in before.items())
    assert not any(p.is_file() for p in migration.rglob("*")) if migration.exists() else True

    model.write_text("corrupt", encoding="utf-8")
    invalid = mod.inventory_one(model)
    assert invalid["exists"] is True and invalid["error"] == "JSONDecodeError"
    model.unlink()
    model.symlink_to(backup)
    result = mod.inventory_one(model)
    assert result["exists"] is False and result["error"] == "symlink_not_followed"
    missing = mod.inventory_one(root / "missing.json")
    assert missing["exists"] is False

print("AI model read-only diagnostics: PASS")
