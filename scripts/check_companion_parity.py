#!/usr/bin/env python3
"""Compare SBC5 native integration contents and version markers across repositories.

Run locally from either repository. The App's embedded bridge must also match.
Checks are read-only; HACS-first updates may run in advisory mode while the
App is being prepared, but the App release gate should enforce strict parity.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

APP_REPO = "krlmdfk/sbc5-control-center"
HACS_REPO = "krlmdfk/sbc5-control-center-integration"
ROOT = Path(__file__).resolve().parents[1]
NATIVE = "custom_components/sbc5_control_center"
BRIDGE = "local_apps/sbc5_control_center/bridge"
APP_RELEASE = "local_apps/sbc5_control_center/release.json"
IGNORED = {".hacs_managed", ".DS_Store"}


def request_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "sbc5-companion-parity",
    })
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def remote_tree(repo: str, ref: str) -> dict:
    ref = urllib.parse.quote(ref, safe="")
    tree = request_json(
        f"https://api.github.com/repos/{repo}/git/trees/{ref}?recursive=1"
    )
    if tree.get("truncated") or not isinstance(tree.get("tree"), list):
        raise RuntimeError(f"Incomplete GitHub tree for {repo}@{ref}")
    return {
        item["path"]: item["sha"]
        for item in tree["tree"]
        if item.get("type") == "blob"
    }


def remote_file(repo: str, ref: str, path: str) -> bytes:
    path = urllib.parse.quote(path, safe="/")
    query = urllib.parse.urlencode({"ref": ref})
    obj = request_json(
        f"https://api.github.com/repos/{repo}/contents/{path}?{query}"
    )
    if obj.get("encoding") != "base64":
        raise RuntimeError(f"Cannot read {repo}/{path}@{ref}")
    return base64.b64decode(obj["content"])


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def local_entries(prefix: str) -> dict[str, str]:
    base = ROOT / prefix
    if not base.is_dir():
        raise RuntimeError(f"Missing local directory: {base}")
    return {
        path.relative_to(base).as_posix(): blob_sha(path.read_bytes())
        for path in base.rglob("*")
        if path.is_file()
        and path.name not in IGNORED
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    }


def remote_entries(tree: dict[str, str], prefix: str) -> dict[str, str]:
    prefix += "/"
    return {
        path[len(prefix):]: sha
        for path, sha in tree.items()
        if path.startswith(prefix)
        and path[len(prefix):] not in IGNORED
    }


def diff(first: dict[str, str], second: dict[str, str], description: str) -> list[str]:
    return [
        f"{description}: {path} ({'missing first' if path not in first else 'missing second' if path not in second else 'different content'})"
        for path in sorted(first.keys() | second.keys())
        if first.get(path) != second.get(path)
    ]


def version_from_const(contents: bytes) -> str:
    match = re.search(
        r'^APP_VERSION\s*=\s*["\x27]([^"\x27]+)["\x27]',
        contents.decode("utf-8"),
        re.M,
    )
    if not match:
        raise RuntimeError("APP_VERSION not found in const.py")
    return match.group(1)


def audit(role: str, app_ref: str, hacs_ref: str) -> list[str]:
    problems: list[str] = []
    if role == "app":
        app_native = local_entries(NATIVE)
        app_bridge = local_entries(BRIDGE)
        hacs_native = remote_entries(remote_tree(HACS_REPO, hacs_ref), NATIVE)
        app_release = json.loads((ROOT / APP_RELEASE).read_text(encoding="utf-8"))
        app_manifest = json.loads((ROOT / NATIVE / "manifest.json").read_text(encoding="utf-8"))
        app_const = (ROOT / NATIVE / "const.py").read_bytes()
        hacs_manifest = json.loads(remote_file(HACS_REPO, hacs_ref, NATIVE + "/manifest.json"))
        hacs_const = remote_file(HACS_REPO, hacs_ref, NATIVE + "/const.py")
    else:
        app_tree = remote_tree(APP_REPO, app_ref)
        app_native = remote_entries(app_tree, NATIVE)
        app_bridge = remote_entries(app_tree, BRIDGE)
        hacs_native = local_entries(NATIVE)
        app_release = json.loads(remote_file(APP_REPO, app_ref, APP_RELEASE))
        app_manifest = json.loads(remote_file(APP_REPO, app_ref, NATIVE + "/manifest.json"))
        app_const = remote_file(APP_REPO, app_ref, NATIVE + "/const.py")
        hacs_manifest = json.loads((ROOT / NATIVE / "manifest.json").read_text(encoding="utf-8"))
        hacs_const = (ROOT / NATIVE / "const.py").read_bytes()

    problems.extend(diff(app_native, hacs_native, "App vs HACS integration"))
    problems.extend(diff(app_native, app_bridge, "App native vs embedded bridge"))

    expected = str(app_release.get("version", ""))
    versions = {
        "App release": expected,
        "App integration manifest": str(app_manifest.get("version", "")),
        "App integration APP_VERSION": version_from_const(app_const),
        "HACS manifest": str(hacs_manifest.get("version", "")),
        "HACS APP_VERSION": version_from_const(hacs_const),
    }
    print("Versions:", ", ".join(f"{key}={value}" for key, value in versions.items()))
    for label, value in versions.items():
        if value != expected:
            problems.append(f"{label}={value}, expected {expected}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=("app", "hacs"))
    parser.add_argument("--app-ref", default="main")
    parser.add_argument("--hacs-ref", default="main")
    parser.add_argument("--advisory", action="store_true")
    args = parser.parse_args()

    try:
        errors = audit(args.role, args.app_ref, args.hacs_ref)
    except Exception as exc:
        errors = [f"Parity check incomplete: {type(exc).__name__}: {exc}"]

    print("Companion parity PASS" if not errors else f"Companion parity DRIFT: {len(errors)} finding(s)")
    for error in errors:
        print(f" - {error}")
        print(f"::{'warning' if args.advisory else 'error'}::{error}")

    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write("### Companion synchronization audit\n\n")
            stream.write(f"Status: {'PASS' if not errors else 'DRIFT'} "
                         f"({'advisory' if args.advisory else 'strict'})\n\n")
            stream.write(f"App: \`{args.app_ref}\` · HACS: \`{args.hacs_ref}\`\n\n")
            for error in errors[:60]:
                stream.write(f"- {error}\n")
    return int(bool(errors) and not args.advisory)


if __name__ == "__main__":
    sys.exit(main())
