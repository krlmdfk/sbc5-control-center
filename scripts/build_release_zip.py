#!/usr/bin/env python3
"""Build the install/update ZIP strictly from update-manifest.json file list."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist")
    args = ap.parse_args()
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    data = json.loads((ROOT / "update-manifest.json").read_text(encoding="utf-8"))
    version = str(data["version"])
    zip_path = out / f"SBC5_Control_Center_v{version}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in data["files"]:
            path = ROOT / rel
            if not path.is_file():
                raise SystemExit(f"Missing release file: {rel}")
            zf.write(path, rel)
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    sha_path = out / f"SBC5_Control_Center_v{version}.sha256"
    sha_path.write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8")
    print(zip_path)
    print(f"SHA256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
