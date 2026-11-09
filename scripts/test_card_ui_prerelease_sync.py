#!/usr/bin/env python3
"""Regression coverage for prerelease Card UI markers in App and Config UI."""

from __future__ import annotations

import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "local_apps" / "sbc5_control_center"
sys.path.insert(0, str(APP))

import dashboard_sync  # noqa: E402
import config_ui  # noqa: E402


def test_normalization(module, source: str, target: str) -> None:
    attr = "current_card_version" if module is dashboard_sync else "current_card_ui_version"
    original = getattr(module, attr)
    setattr(module, attr, lambda: target)
    try:
        card = {
            "type": "vertical-stack",
            "cards": [
                {
                    "type": "markdown",
                    "content": (
                        f"Card UI v{source} | "
                        f"Update Card v{source} | "
                        f"SBC5CC {source}"
                    ),
                },
                {
                    "type": "markdown",
                    "content": "Other software v3.2.0 remains unchanged.",
                },
            ],
        }
        normalized = module._runtime_versioned_card(card)
        marker = normalized["cards"][0]["content"]
        assert marker == (
            f"Card UI v{target} | Update Card v{target} | SBC5CC {target}"
        ), (module.__name__, source, target, marker)
        assert normalized["cards"][1] == card["cards"][1]
        assert module._runtime_versioned_card(normalized) == normalized, (
            module.__name__,
            "version normalization must be idempotent",
        )
        if module is dashboard_sync:
            assert module._card_version(normalized) == target
    finally:
        setattr(module, attr, original)


def main() -> None:
    scenarios = [
        ("3.2.0", "3.2.1-rc2"),
        ("3.2.1-rc2", "3.2.1-rc2"),
        ("3.2.1-rc2-rc2", "3.2.1-rc2"),
        ("3.2.1-rc2", "3.2.0"),
        ("3.2.1-beta.2+git.abc", "3.2.1-rc2"),
        ("3.2.0", "3.2.1-beta.2+git.abc"),
    ]
    for module in (dashboard_sync, config_ui):
        for source, target in scenarios:
            test_normalization(module, source, target)
    print("Card UI prerelease synchronization: PASS")


if __name__ == "__main__":
    main()
