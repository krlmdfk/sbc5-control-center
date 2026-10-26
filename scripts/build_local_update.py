#!/usr/bin/env python3
"""Build and verify the SBC5 local-update ZIP from update-manifest.json.

The manifest is the file allow-list. Hidden paths such as .github are handled exactly
like normal paths, preventing shell-glob omissions in release packages.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "update-manifest.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_manifest() -> dict:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = data.get("files")
    if not isinstance(files, dict) or not files:
        raise SystemExit("update-manifest.json: missing non-empty files mapping")
    return data


def build(output: Path) -> tuple[str, int]:
    data = load_manifest()
    files: dict[str, str] = data["files"]
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    tmp.unlink(missing_ok=True)

    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in sorted(files):
            path = ROOT / rel
            if not path.is_file():
                raise SystemExit(f"Manifest file missing while packaging: {rel}")
            raw = path.read_bytes()
            got = sha256_bytes(raw)
            if got != files[rel]:
                raise SystemExit(f"Manifest hash mismatch before packaging: {rel}")
            zf.writestr(rel, raw)
        zf.writestr("update-manifest.json", MANIFEST.read_bytes())

    tmp.replace(output)
    verify(output)
    return sha256_bytes(output.read_bytes()), len(files)


def verify(archive: Path) -> None:
    data = load_manifest()
    files: dict[str, str] = data["files"]
    with zipfile.ZipFile(archive) as zf:
        names = set(zf.namelist())
        required = set(files) | {"update-manifest.json"}
        missing = sorted(required - names)
        if missing:
            raise SystemExit("Local-update ZIP missing files:\n" + "\n".join(f"- {x}" for x in missing))
        embedded = json.loads(zf.read("update-manifest.json").decode("utf-8"))
        if embedded != data:
            raise SystemExit("Embedded update-manifest.json differs from repository manifest")
        bad: list[str] = []
        for rel, wanted in files.items():
            got = sha256_bytes(zf.read(rel))
            if got != wanted:
                bad.append(rel)
        if bad:
            raise SystemExit("Local-update ZIP hash mismatch:\n" + "\n".join(f"- {x}" for x in bad))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ap.add_argument("--verify-only", action="store_true")
    args = ap.parse_args()
    requested = Path(args.output).expanduser()
    parent = requested.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    if not parent.is_dir() or not os.access(parent, os.W_OK):
        fallback = Path(os.environ.get("TMPDIR") or tempfile.gettempdir())
        fallback.mkdir(parents=True, exist_ok=True)
        output = (fallback / requested.name).resolve()
        print(f"Output directory {parent} is not writable; using platform temporary directory: {output}")
    else:
        output = requested.resolve()
    if args.verify_only:
        verify(output)
        print(f"Local-update ZIP verification PASS — {output}")
        return 0
    digest, count = build(output)
    print(f"Local-update ZIP PASS — files {count}/{count}; sha256={digest}; output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
