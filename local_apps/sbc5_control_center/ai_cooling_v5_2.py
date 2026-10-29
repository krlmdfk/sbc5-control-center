#!/usr/bin/env python3
"""SBC5 AI Cooling v5.2 — Thermal Predictor Active Assist."""
from __future__ import annotations

import importlib.util
from pathlib import Path


def _base_path() -> Path:
    runtime = Path("/ai_cooling_v5_1.py")
    if runtime.is_file():
        return runtime
    return Path(__file__).with_name("ai_cooling_v5_1.py")


def _load_base():
    path = _base_path()
    spec = importlib.util.spec_from_file_location("sbc5_ai_cooling_v5_1_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load AI Cooling v5.1 base module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


layer = _load_base()


def main() -> int:
    return layer.main()


if __name__ == "__main__":
    raise SystemExit(main())
