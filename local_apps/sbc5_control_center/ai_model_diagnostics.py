#!/usr/bin/env python3
"""Read-only SBC5 AI model preservation inventory.

Does not reset, migrate, rewrite, recover, or expose full learned model contents.
Use only in a trusted App terminal; logs include file hashes and counts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def inventory_one(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(path), "exists": False}
    try:
        if path.is_symlink():
            result["error"] = "symlink_not_followed"
            return result
        if not path.is_file():
            if path.exists():
                result["error"] = "not_a_regular_file"
            return result
        result["exists"] = True
        raw = path.read_bytes()
        result["bytes"] = len(raw)
        result["sha256"] = hashlib.sha256(raw).hexdigest()
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            result["error"] = "not_a_json_object"
            return result
        legacy = parsed.get("legacy_workload_v1")
        legacy = legacy if isinstance(legacy, dict) else {}
        result["schema"] = parsed.get("schema")
        for field in ("observations_total", "qualified_samples_total",
                      "legacy_samples_total", "migrated_from_schema"):
            value = parsed.get(field)
            if isinstance(value, int) and not isinstance(value, bool):
                result[field] = value
        for field in ("observations_total", "qualified_samples_total"):
            value = legacy.get(field)
            if isinstance(value, int) and not isinstance(value, bool):
                result["legacy_" + field] = value
        hierarchical = parsed.get("hierarchical_v5")
        result["has_hierarchical_v5"] = isinstance(hierarchical, dict)
        result["has_thermal_predictor"] = isinstance(parsed.get("thermal_predictor"), dict)
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        # Avoid logging raw file content or exception paths.
        result["error"] = type(exc).__name__
    return result


def inventory(
    model: Path,
    backup_dir: Path,
    migration_backups: Path,
    legacy_export: Path,
    limit: int = 12,
) -> dict[str, Any]:
    collected: list[Path] = []
    for base, pattern in (
        (backup_dir, "ai_cooling_model_*.json"),
        (migration_backups, "store_import_*/ai_cooling_model.json"),
    ):
        if base.is_dir() and not base.is_symlink():
            try:
                collected.extend(p for p in base.glob(pattern) if not p.is_symlink())
            except OSError:
                pass
    if legacy_export.is_file() or legacy_export.is_symlink():
        collected.append(legacy_export)
    # Limit IO and avoid duplicate paths in public diagnostics.
    candidates = sorted(set(collected), key=lambda p: str(p), reverse=True)[:limit]
    return {
        "active_model": inventory_one(model),
        "candidate_backups": [inventory_one(p) for p in candidates],
        "candidate_count_shown": len(candidates),
        "note": "Read-only inventory; counters cannot prove model quality or recover lost samples.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", type=Path, default=Path("/data/ai_cooling_model.json"))
    ap.add_argument("--backups", type=Path, default=Path("/data/ai_model_backups"))
    ap.add_argument("--migration-backups", type=Path, default=Path("/data/migration_backups"))
    ap.add_argument("--legacy-export", type=Path, default=Path(
        "/homeassistant/sbc5_control_center/migration/data_export/ai_cooling_model.json"
    ))
    ap.add_argument("--limit", type=int, default=12)
    args = ap.parse_args()
    report = inventory(
        args.model, args.backups, args.migration_backups, args.legacy_export,
        limit=min(30, max(0, args.limit)),
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
