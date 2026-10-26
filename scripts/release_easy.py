#!/usr/bin/env python3
"""SBC5 two-phase release helper for Termux/Linux.

prepare: pull both repos, bump main version, render HACS repo, validate, commit both.
publish: after green CI, push annotated tags and optionally create GitHub Releases via gh.
"""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
DEFAULT_HACS = Path.home() / "sbc5-hacs-publish" / "sbc5-control-center-integration"


def run(cmd, cwd=ROOT, check=True):
    print("+", " ".join(map(str, cmd)))
    return subprocess.run(cmd, cwd=cwd, check=check, text=True)


def out(cmd, cwd=ROOT):
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def clean(repo: Path) -> bool:
    return not out(["git", "status", "--porcelain"], repo)


def require_clean(repo: Path, label: str):
    if not clean(repo):
        raise SystemExit(f"{label} has uncommitted changes:\n" + out(["git", "status", "--short"], repo))


def current_version() -> str:
    return str(json.loads((APP / "release.json").read_text(encoding="utf-8"))["version"])


def prepare(args) -> int:
    hacs = Path(args.hacs_repo).expanduser().resolve()
    require_clean(ROOT, "Main repository")
    require_clean(hacs, "HACS repository")

    run(["git", "pull", "--ff-only", "origin", "main"], ROOT)
    run(["git", "pull", "--ff-only", "origin", "main"], hacs)

    run([
        "python", "scripts/release_prepare.py",
        "--version", args.version,
        "--restart-required", args.restart,
        "--summary-en", args.summary_en,
        "--summary-pl", args.summary_pl,
    ], ROOT)
    run(["python", "scripts/render_hacs_release.py", "--repo", str(hacs), "--summary-en", args.summary_en, "--summary-pl", args.summary_pl], ROOT)
    run(["python", "scripts/update_manifest_hashes.py"], ROOT)
    run(["python", "scripts/validate_release.py"], ROOT)
    run(["git", "diff", "--check"], ROOT)
    run(["git", "diff", "--check"], hacs)

    run(["git", "add", "-A"], ROOT)
    run(["git", "commit", "-m", f"Release {args.version}"], ROOT)
    run(["git", "add", "-A"], hacs)
    run(["git", "commit", "-m", f"Release {args.version}"], hacs)

    if args.push:
        run(["git", "push", "origin", "main"], ROOT)
        run(["git", "push", "origin", "main"], hacs)
        print("\nPushed both main branches. Wait for green CI, then run publish.")
    else:
        print("\nPrepared and committed both repositories.")
        print("Push when ready:")
        print(f"  cd {ROOT} && git push origin main")
        print(f"  cd {hacs} && git push origin main")
    return 0


def ensure_remote_head(repo: Path):
    run(["git", "fetch", "origin"], repo)
    head = out(["git", "rev-parse", "HEAD"], repo)
    remote = out(["git", "rev-parse", "origin/main"], repo)
    if head != remote:
        raise SystemExit(f"{repo}: HEAD is not origin/main; refusing to tag")


def tag_and_push(repo: Path, version: str, message: str):
    # Refuse accidental retagging.
    local_tags = out(["git", "tag", "--list", version], repo)
    if local_tags:
        raise SystemExit(f"{repo}: tag {version} already exists locally")
    run(["git", "tag", "-a", version, "-m", message], repo)
    run(["git", "push", "origin", version], repo)


def publish(args) -> int:
    hacs = Path(args.hacs_repo).expanduser().resolve()
    require_clean(ROOT, "Main repository")
    require_clean(hacs, "HACS repository")
    expect = current_version()
    if args.version != expect:
        raise SystemExit(f"Requested tag {args.version}, but current main release is {expect}")
    ensure_remote_head(ROOT)
    ensure_remote_head(hacs)

    tag_and_push(ROOT, args.version, f"SBC5 Control Center {args.version}")
    tag_and_push(hacs, args.version, f"SBC5 Control Center Integration {args.version}")

    if args.github_release:
        if not shutil.which("gh"):
            raise SystemExit("gh CLI is not installed; tags are pushed, but GitHub Releases were not created")
        run(["gh", "release", "create", args.version, "--title", f"SBC5 Control Center {args.version}", "--notes-file", f"RELEASE_NOTES_{args.version}.md"], ROOT)
        run(["gh", "release", "create", args.version, "--title", f"SBC5 Control Center Integration {args.version}", "--notes-file", f"RELEASE_NOTES_{args.version}.md"], hacs)
    else:
        print("Tags pushed. Create GitHub Releases from the two RELEASE_NOTES files, or rerun with --github-release when gh is configured.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prepare")
    p.add_argument("--version", required=True)
    p.add_argument("--summary-en", required=True)
    p.add_argument("--summary-pl", required=True)
    p.add_argument("--restart", choices=["none", "home_assistant", "host"], default="home_assistant")
    p.add_argument("--hacs-repo", default=str(DEFAULT_HACS))
    p.add_argument("--push", action="store_true")
    p.set_defaults(func=prepare)

    p = sub.add_parser("publish")
    p.add_argument("--version", required=True)
    p.add_argument("--hacs-repo", default=str(DEFAULT_HACS))
    p.add_argument("--github-release", action="store_true")
    p.set_defaults(func=publish)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
