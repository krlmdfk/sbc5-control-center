#!/usr/bin/env python3
"""Cooperative cross-process lock for durable SBC5 AI model transactions.

Never remove the lock file: its inode must remain stable across reset/recreate.
The lock protects the complete multi-layer evaluator step, not just os.replace.
"""
from __future__ import annotations

import contextlib
import fcntl
import os
import stat
import time
from pathlib import Path

AI_MODEL_LOCK_PATH = Path("/data/ai_cooling_model.lock")


@contextlib.contextmanager
def ai_model_lock(lock_path: Path | str | None = None, *, timeout_seconds: float = 8.0):
    path = Path(lock_path) if lock_path is not None else AI_MODEL_LOCK_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    acquired = False
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
            raise OSError("SBC5 AI lock must be a normal unlinked-from-alias file")
        os.fchmod(fd, 0o600)
        deadline = time.monotonic() + max(0.0, float(timeout_seconds))
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("SBC5 AI model transaction lock timed out; model unchanged")
                time.sleep(0.05)
        yield
    finally:
        if acquired:
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
