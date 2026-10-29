#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "local_apps" / "sbc5_control_center" / "ethernet_guard.py"

spec = importlib.util.spec_from_file_location("sbc5_ethernet_guard", MODULE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_add_remove_idempotence() -> None:
    original = "# user config\narm_64bit=1\n"
    off, external_off, external_on = mod.desired_boot_text(original, "off")
    assert not external_off and not external_on
    assert off.count(mod.MARK_BEGIN) == 1
    assert off.count(mod.EEE_LINE) == 1

    off2, _, _ = mod.desired_boot_text(off, "off")
    assert off2 == off, "EEE off must be idempotent"

    auto, _, _ = mod.desired_boot_text(off, "auto")
    assert auto == original, "auto must remove only the SBC5-owned block"


def test_external_off_is_preserved() -> None:
    original = "dtparam=eee=off\n# keep me\n"
    desired, external_off, external_on = mod.desired_boot_text(original, "off")
    assert external_off and not external_on
    assert desired == original
    assert mod.MARK_BEGIN not in desired


def test_external_on_is_detected() -> None:
    original = "dtparam=eee=on\n"
    external_off, external_on = mod.external_eee_state(original)
    assert not external_off and external_on
    guard_text = MODULE.read_text(encoding="utf-8")
    assert "Conflicting external dtparam=eee=on" in guard_text
    assert "left config.txt unchanged" in guard_text


def test_flap_window_pruning() -> None:
    events = deque([10.0, 40.0, 80.0, 100.0])
    mod.prune_events(events, 50, 100.0)
    assert list(events) == [80.0, 100.0]


def test_release_wiring() -> None:
    docker = (ROOT / "local_apps" / "sbc5_control_center" / "Dockerfile").read_text(encoding="utf-8")
    run = (ROOT / "local_apps" / "sbc5_control_center" / "run.sh").read_text(encoding="utf-8")
    config = (ROOT / "local_apps" / "sbc5_control_center" / "config.yaml").read_text(encoding="utf-8")
    assert "COPY ethernet_guard.py /ethernet_guard.py" in docker
    assert 'ETHERNET_GUARD="/ethernet_guard.py"' in run
    assert "ethernet_eee_mode: list(auto|off)" in config
    assert "ethernet_health_monitor_enabled: bool" in config


def main() -> int:
    test_add_remove_idempotence()
    test_external_off_is_preserved()
    test_external_on_is_detected()
    test_flap_window_pruning()
    test_release_wiring()
    print("Ethernet EEE stability tests PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
