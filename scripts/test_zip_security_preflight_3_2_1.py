#!/usr/bin/env python3
"""Regression tests: never extract a malformed SBC5 local-update ZIP."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "local_apps/sbc5_control_center/zip_security_preflight.py"
spec = importlib.util.spec_from_file_location("zip_security_preflight", SCRIPT)
assert spec is not None and spec.loader is not None
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

GOOD = {
    "local_apps/sbc5_control_center/run.sh": b"safe bootstrap",
    "local_apps/sbc5_control_center/config.yaml": b"version: test\n",
    "packages/sbc5_control_center.yaml": b"safe package",
}


def make_manifest(files: dict[str, bytes]) -> bytes:
    return json.dumps({
        "version": "test",
        "files": {name: hashlib.sha256(body).hexdigest() for name, body in files.items()},
    }).encode()


def build_zip(path: Path, *, members: list[tuple[str | zipfile.ZipInfo, bytes]],
              prefix: str = "", listed: dict[str, bytes] | None = None) -> None:
    files = GOOD if listed is None else listed
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as arc:
        arc.writestr(prefix + "update-manifest.json", make_manifest(files))
        for name, body in members:
            arc.writestr((prefix + name) if isinstance(name, str) else name, body)


def should_reject(path: Path, reason: str) -> None:
    try:
        checker.validate_archive(path)
    except checker.UnsafeUpdateArchive:
        return
    raise AssertionError(f"accepted invalid {reason}")


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    good = td / "good.zip"
    build_zip(good, members=list(GOOD.items()))
    checker.validate_archive(good)
    assert checker.main.__name__ == "main"

    wrapped = td / "wrapped.zip"
    build_zip(wrapped, prefix="SBC5_Control_Center/", members=list(GOOD.items()))
    checker.validate_archive(wrapped)

    bad_names = [
        "../escape.txt", "/absolute.txt", "dir/../../escape.txt", r"dir\escape.txt",
        "C:/device.txt", "./bad.txt", "name//bad", "name\nbad"
    ]
    for i, bad in enumerate(bad_names):
        path = td / f"bad_name_{i}.zip"
        build_zip(path, members=[*GOOD.items(), (bad, b"extra")])
        should_reject(path, bad)

    for reason, members, listed in [
        ("unlisted", [*GOOD.items(), ("unlisted.txt", b"extra")], None),
        ("missing", list(GOOD.items())[:-1], None),
        ("tampered", [(name, body + b"modified" if idx == 0 else body)
                      for idx, (name, body) in enumerate(GOOD.items())], None),
        ("empty manifest map", list(GOOD.items()), {}),
    ]:
        path = td / (reason.replace(" ", "_") + ".zip")
        build_zip(path, members=members, listed=listed)
        should_reject(path, reason)

    extra_dir = td / "undeclared_directory.zip"
    with zipfile.ZipFile(extra_dir, "w") as arc:
        arc.writestr("update-manifest.json", make_manifest(GOOD))
        for name, body in GOOD.items():
            arc.writestr(name, body)
        arc.writestr("unlisted_empty_directory/", b"")
    should_reject(extra_dir, "undeclared directory")

    listed_dirs = td / "declared_directories.zip"
    with zipfile.ZipFile(listed_dirs, "w") as arc:
        arc.writestr("update-manifest.json", make_manifest(GOOD))
        arc.writestr("local_apps/", b"")
        arc.writestr("local_apps/sbc5_control_center/", b"")
        arc.writestr("packages/", b"")
        for name, body in GOOD.items():
            arc.writestr(name, body)
    checker.validate_archive(listed_dirs)

    dup = td / "duplicate.zip"
    with zipfile.ZipFile(dup, "w") as arc:
        arc.writestr("update-manifest.json", make_manifest(GOOD))
        for name, body in GOOD.items():
            arc.writestr(name, body)
        arc.writestr(next(iter(GOOD)), b"duplicate")
    should_reject(dup, "duplicate name")

    symlink = td / "symlink.zip"
    link = zipfile.ZipInfo("link")
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    build_zip(symlink, members=[*GOOD.items(), (link, b"/etc/passwd")])
    should_reject(symlink, "symbolic link")

    special = td / "special.zip"
    device = zipfile.ZipInfo("device")
    device.create_system = 3
    device.external_attr = (stat.S_IFCHR | 0o644) << 16
    build_zip(special, members=[*GOOD.items(), (device, b"x")])
    should_reject(special, "special file")

    # Declared uncompressed size is rejected before any filesystem extraction.
    huge = zipfile.ZipInfo("large.dat")
    huge.file_size = checker.MAX_MEMBER_UNCOMPRESSED + 1
    try:
        checker._safe_info(huge)
    except checker.UnsafeUpdateArchive:
        pass
    else:
        raise AssertionError("oversized entry accepted")

    runtime = (ROOT / "local_apps/sbc5_control_center/run_legacy.sh").read_text()
    extract = runtime.index('unzip -q "$snapshot" -d "$stage"')
    assert runtime.index('python3 /zip_security_preflight.py "$snapshot"') < extract
    assert runtime.count('python3 /zip_security_preflight.py "$zip"') == 1
    assert runtime.count('python3 /zip_security_preflight.py "$snapshot"') == 1
    # The mutating archive stays untouched while the preflight inspects a
    # private frozen-in-practice copy, preventing a scan/extract substitution.
    install = runtime[runtime.index('install_local_update() ('): ]
    assert 'snapshot_dir="$(mktemp -d /tmp/sbc5_update.XXXXXXXX)"' in install
    assert 'snapshot="$snapshot_dir/candidate.zip"' in install
    assert 'cp -- "$zip" "$snapshot"' in install
    assert install.index('cp -- "$zip" "$snapshot"') < install.index('python3 /zip_security_preflight.py "$snapshot"') < install.index('unzip -q "$snapshot" -d "$stage"')
    assert 'verify_local_update_package "$snapshot" "$stage" "$root" "$manifest_file"' in install
    assert 'rm -rf -- "$snapshot_dir"' in install
    scan_start = runtime.index('scan_local_update_candidate() {')
    verify_start = runtime.index('verify_local_update_package() {')
    scanner = runtime[scan_start:verify_start]
    assert scanner.index('python3 /zip_security_preflight.py "$zip"') < scanner.index('unzip -Z1 "$zip"')
    docker = (ROOT / "local_apps/sbc5_control_center/Dockerfile").read_text()
    assert "COPY zip_security_preflight.py /zip_security_preflight.py" in docker

print("SBC5 ZIP pre-extraction security regression: PASS")
