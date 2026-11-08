#!/usr/bin/env python3
"""Reject malformed or unexpected SBC5 update ZIP content before extraction.

This is an untrusted-input preflight, not an authenticity/signature check.
Full compatibility/version and post-extraction verification remains in run_legacy.sh.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat
import sys
import zipfile

MAX_ENTRIES = 4096
MAX_TOTAL_UNCOMPRESSED = 512 * 1024 * 1024
MAX_MEMBER_UNCOMPRESSED = 128 * 1024 * 1024
MAX_MANIFEST_BYTES = 2 * 1024 * 1024
CHUNK = 1024 * 1024


class UnsafeUpdateArchive(ValueError):
    """ZIP must not be extracted or installed."""


def _valid_name(name: str, *, directory: bool) -> None:
    if not name or name.startswith("/") or "\\" in name:
        raise UnsafeUpdateArchive("absolute, empty or backslash ZIP path")
    trimmed = name[:-1] if directory else name
    if not trimmed or any(part in ("", ".", "..") for part in trimmed.split("/")):
        raise UnsafeUpdateArchive("unsafe relative ZIP path")
    if re.match(r"^[A-Za-z]:", trimmed):
        raise UnsafeUpdateArchive("Windows drive ZIP path")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in name):
        raise UnsafeUpdateArchive("control character in ZIP path")


def _safe_info(info: zipfile.ZipInfo) -> None:
    _valid_name(info.filename, directory=info.is_dir())
    if info.flag_bits & 1:
        raise UnsafeUpdateArchive("encrypted ZIP member")
    mode = info.external_attr >> 16
    kind = stat.S_IFMT(mode)
    allowed_kind = stat.S_IFDIR if info.is_dir() else stat.S_IFREG
    if kind not in (0, allowed_kind):
        raise UnsafeUpdateArchive("symlink or special ZIP member")
    if info.file_size > MAX_MEMBER_UNCOMPRESSED:
        raise UnsafeUpdateArchive("oversized ZIP member")
    if info.file_size > 1024 * 1024 and info.file_size > max(1, info.compress_size) * 2000:
        raise UnsafeUpdateArchive("excessive ZIP decompression ratio")


def _read_limited(archive: zipfile.ZipFile, info: zipfile.ZipInfo, limit: int) -> bytes:
    if info.file_size > limit:
        raise UnsafeUpdateArchive("oversized ZIP manifest")
    with archive.open(info) as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise UnsafeUpdateArchive("oversized ZIP manifest")
    return data


def validate_archive(path: str | Path) -> None:
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if not infos or len(infos) > MAX_ENTRIES:
            raise UnsafeUpdateArchive("empty ZIP or excessive number of members")

        members: dict[str, zipfile.ZipInfo] = {}
        uncompressed = 0
        for info in infos:
            _safe_info(info)
            if info.filename in members:
                raise UnsafeUpdateArchive("duplicate ZIP member")
            members[info.filename] = info
            uncompressed += info.file_size
            if uncompressed > MAX_TOTAL_UNCOMPRESSED:
                raise UnsafeUpdateArchive("excessive total uncompressed ZIP size")

        manifest_names = [
            name for name, info in members.items()
            if not info.is_dir() and (name == "update-manifest.json" or name.endswith("/update-manifest.json"))
        ]
        if len(manifest_names) != 1:
            raise UnsafeUpdateArchive("exactly one update manifest is required")

        manifest_name = manifest_names[0]
        prefix = manifest_name[: -len("update-manifest.json")]
        try:
            manifest = json.loads(_read_limited(archive, members[manifest_name], MAX_MANIFEST_BYTES))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise UnsafeUpdateArchive("invalid update manifest JSON") from exc
        if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict) or not manifest["files"]:
            raise UnsafeUpdateArchive("manifest file allow-list missing")
        if len(manifest["files"]) + 1 > MAX_ENTRIES:
            raise UnsafeUpdateArchive("manifest allow-list too large")

        expected: set[str] = {manifest_name}
        for rel, digest in manifest["files"].items():
            if not isinstance(rel, str) or not isinstance(digest, str):
                raise UnsafeUpdateArchive("invalid manifest path or SHA-256")
            _valid_name(rel, directory=False)
            if not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
                raise UnsafeUpdateArchive("invalid manifest SHA-256")
            expected.add(prefix + rel)

        actual = {name for name, info in members.items() if not info.is_dir()}
        if actual != expected:
            raise UnsafeUpdateArchive("ZIP members differ from manifest allow-list")

        for name, info in members.items():
            if info.is_dir() and not (name == prefix or name.startswith(prefix)):
                raise UnsafeUpdateArchive("directory outside ZIP package root")

        # Validate every ZIP data stream and every digest before extracting any member.
        for rel, expected_digest in manifest["files"].items():
            info = members[prefix + rel]
            hasher = hashlib.sha256()
            size = 0
            with archive.open(info) as stream:
                while block := stream.read(CHUNK):
                    size += len(block)
                    if size > MAX_MEMBER_UNCOMPRESSED:
                        raise UnsafeUpdateArchive("ZIP member exceeds uncompressed limit")
                    hasher.update(block)
            if size != info.file_size or hasher.hexdigest().lower() != expected_digest.lower():
                raise UnsafeUpdateArchive("ZIP content failed SHA-256 verification")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: zip_security_preflight.py UPDATE.zip", file=sys.stderr)
        return 2
    try:
        validate_archive(sys.argv[1])
    except (UnsafeUpdateArchive, OSError, zipfile.BadZipFile, RuntimeError, EOFError, ValueError) as exc:
        print(f"SBC5 ZIP preflight rejected archive: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
