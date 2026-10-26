#!/usr/bin/env python3
"""Rebuild SHA-256 values for files already tracked by update-manifest.json."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "update-manifest.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = data.get("files")
    if not isinstance(files, dict) or not files:
        raise SystemExit("update-manifest.json: missing non-empty 'files' mapping")

    missing: list[str] = []
    for rel in list(files):
        p = ROOT / rel
        if not p.is_file():
            missing.append(rel)
            continue
        files[rel] = sha256(p)

    if missing:
        raise SystemExit("Missing manifest files:\n" + "\n".join(f"- {x}" for x in missing))

    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"update-manifest hashes rebuilt: {len(files)}/{len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
