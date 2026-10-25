#!/usr/bin/env python3
"""Rebuild SHA-256 values for files already tracked by update-manifest.json."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    manifest_path = root / "update-manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    missing: list[str] = []
    for rel in list(data.get("files", {})):
        path = root / rel
        if not path.is_file():
            missing.append(rel)
            continue
        data["files"][rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    if missing:
        raise SystemExit("Missing manifest files:\n" + "\n".join(missing))
    manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"update-manifest: rebuilt {len(data['files'])} SHA-256 values")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
