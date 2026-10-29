#!/usr/bin/env python3
"""SBC5 Ethernet Stability Guard.

Owns only the SBC5-managed EEE boot block and lightweight end0 health telemetry.
It intentionally runs outside the legacy cooling/control plane.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

APP_VERSION = os.environ.get("SBC5CC_APP_VERSION", "unknown")
OPTIONS_PATH = Path("/data/options.json")
STATE_DATA_PATH = Path("/data/ethernet_health.json")
STATE_HA_PATH = Path("/homeassistant/sbc5_control_center/ethernet_health.json")
BACKUP_DIR = Path("/data/boot_config_backups")

MARK_BEGIN = "# BEGIN SBC5 CONTROL CENTER ETHERNET STABILITY"
MARK_END = "# END SBC5 CONTROL CENTER ETHERNET STABILITY"
EEE_LINE = "dtparam=eee=off"

BOOT_CANDIDATES = (
    Path("/proc/1/root/mnt/boot/config.txt"),
    Path("/proc/1/root/boot/firmware/config.txt"),
    Path("/proc/1/root/boot/config.txt"),
    Path("/mnt/boot/config.txt"),
    Path("/boot/firmware/config.txt"),
    Path("/boot/config.txt"),
)

SYSFS_CANDIDATES = (
    Path("/proc/1/root/sys/class/net/end0"),
    Path("/sys/class/net/end0"),
)

DEFAULTS = {
    "ethernet_eee_mode": "auto",
    "ethernet_health_monitor_enabled": True,
    "ethernet_flap_window_minutes": 60,
    "ethernet_flap_degraded_threshold": 3,
}

BLOCK_RE = re.compile(
    rf"(?ms)^[ \t]*{re.escape(MARK_BEGIN)}[ \t]*\n.*?^[ \t]*{re.escape(MARK_END)}[ \t]*(?:\n|$)"
)
EXTERNAL_EEE_OFF_RE = re.compile(r"(?mi)^[ \t]*dtparam[ \t]*=[ \t]*eee[ \t]*=[ \t]*off[ \t]*(?:#.*)?$")
EXTERNAL_EEE_ON_RE = re.compile(r"(?mi)^[ \t]*dtparam[ \t]*=[ \t]*eee[ \t]*=[ \t]*on[ \t]*(?:#.*)?$")


def log(message: str) -> None:
    print(f"[SBC5 Ethernet] {message}", flush=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return default


def atomic_json_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def load_options() -> dict:
    raw = read_json(OPTIONS_PATH, {})
    if not isinstance(raw, dict):
        raw = {}
    out = dict(DEFAULTS)
    out.update({k: raw.get(k, v) for k, v in DEFAULTS.items()})

    mode = str(out.get("ethernet_eee_mode", "auto")).strip().lower()
    out["ethernet_eee_mode"] = mode if mode in {"auto", "off"} else "auto"
    out["ethernet_health_monitor_enabled"] = bool(out.get("ethernet_health_monitor_enabled", True))
    try:
        out["ethernet_flap_window_minutes"] = min(1440, max(1, int(out.get("ethernet_flap_window_minutes", 60))))
    except (TypeError, ValueError):
        out["ethernet_flap_window_minutes"] = 60
    try:
        out["ethernet_flap_degraded_threshold"] = min(50, max(1, int(out.get("ethernet_flap_degraded_threshold", 3))))
    except (TypeError, ValueError):
        out["ethernet_flap_degraded_threshold"] = 3
    return out


def find_boot_config() -> Path | None:
    for path in BOOT_CANDIDATES:
        try:
            if path.is_file() and os.access(path, os.R_OK):
                return path
        except OSError:
            continue
    return None


def current_boot_id() -> str:
    for path in (
        Path("/proc/1/root/proc/sys/kernel/random/boot_id"),
        Path("/proc/sys/kernel/random/boot_id"),
    ):
        try:
            value = path.read_text(encoding="utf-8").strip()
            if value:
                return value
        except OSError:
            continue
    return "unknown"


def managed_block(text: str) -> str | None:
    match = BLOCK_RE.search(text)
    return match.group(0) if match else None


def strip_managed_block(text: str) -> str:
    new = BLOCK_RE.sub("", text)
    return new.rstrip() + ("\n" if new.strip() else "")


def text_without_managed_block(text: str) -> str:
    return BLOCK_RE.sub("", text)


def external_eee_state(text: str) -> tuple[bool, bool]:
    outside = text_without_managed_block(text)
    return bool(EXTERNAL_EEE_OFF_RE.search(outside)), bool(EXTERNAL_EEE_ON_RE.search(outside))


def desired_boot_text(current: str, mode: str) -> tuple[str, bool, bool]:
    base = strip_managed_block(current)
    external_off, external_on = external_eee_state(current)

    if mode == "off":
        # Never duplicate or claim ownership of a user's existing EEE-off line.
        if external_off:
            desired = base
        else:
            block = f"{MARK_BEGIN}\n{EEE_LINE}\n{MARK_END}\n"
            desired = base.rstrip() + ("\n\n" if base.strip() else "") + block
    else:
        # Auto relinquishes SBC5 ownership; user-managed EEE lines are preserved.
        desired = base

    if desired and not desired.endswith("\n"):
        desired += "\n"
    return desired, external_off, external_on


def backup_boot_file(path: Path) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    target = BACKUP_DIR / f"config.txt.ethernet-{stamp}.bak"
    shutil.copy2(path, target)
    return target


def atomic_text_replace(path: Path, content: str) -> None:
    directory = path.parent
    fd, tmp_name = tempfile.mkstemp(prefix=".sbc5-ethernet-", suffix=".tmp", dir=str(directory))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.chmod(tmp, path.stat().st_mode & 0o777)
        except OSError:
            pass
        os.replace(tmp, path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def update_boot_config(mode: str) -> dict:
    path = find_boot_config()
    result = {
        "boot_config_available": bool(path),
        "boot_config_path": str(path or ""),
        "requested_mode": mode,
        "configured_off": False,
        "configuration_source": "unavailable",
        "external_eee_off": False,
        "external_eee_on": False,
        "write_changed": False,
        "write_verified": False,
        "backup_path": "",
        "error": "",
    }
    if path is None:
        result["error"] = "No readable host config.txt found"
        return result

    try:
        current = path.read_text(encoding="utf-8")
    except OSError as exc:
        result["error"] = f"read failed: {exc}"
        return result

    external_off, external_on = external_eee_state(current)
    result["external_eee_off"] = external_off
    result["external_eee_on"] = external_on
    if mode == "off" and external_on and not external_off:
        result["error"] = "Conflicting external dtparam=eee=on; SBC5 left config.txt unchanged"
        log(result["error"])
        return result
    if mode == "off" and external_on and external_off:
        result["error"] = "Conflicting external dtparam=eee=on/off entries; SBC5 left config.txt unchanged"
        log(result["error"])
        return result

    desired, external_off, external_on = desired_boot_text(current, mode)

    if desired != current:
        try:
            if not os.access(path, os.W_OK):
                result["error"] = "Host config.txt is not writable"
                return result
            backup = backup_boot_file(path)
            atomic_text_replace(path, desired)
            result["write_changed"] = True
            result["backup_path"] = str(backup)
            verify = path.read_text(encoding="utf-8")
            if verify != desired:
                raise OSError("post-write verification mismatch")
            result["write_verified"] = True
            log(f"config.txt changed for EEE mode={mode}; backup={backup.name}; host restart required.")
        except OSError as exc:
            result["error"] = f"write failed: {exc}"
            log(result["error"])
            return result

    try:
        final = path.read_text(encoding="utf-8")
    except OSError:
        final = desired

    outside_off, outside_on = external_eee_state(final)
    block = managed_block(final) or ""
    managed_off = EEE_LINE in block
    result["configured_off"] = managed_off or outside_off
    result["external_eee_off"] = outside_off
    result["external_eee_on"] = outside_on
    if managed_off:
        result["configuration_source"] = "sbc5_managed"
    elif outside_off:
        result["configuration_source"] = "external"
    else:
        result["configuration_source"] = "default"
    return result


def read_sysfs_value(root: Path, name: str) -> str:
    try:
        return (root / name).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def find_end0_sysfs() -> Path | None:
    for root in SYSFS_CANDIDATES:
        try:
            if root.is_dir():
                return root
        except OSError:
            continue
    return None


def read_link() -> dict:
    root = find_end0_sysfs()
    if root is None:
        return {"interface": "end0", "available": False, "carrier": None, "operstate": "unavailable", "speed_mbps": None, "duplex": ""}

    carrier_raw = read_sysfs_value(root, "carrier")
    carrier = True if carrier_raw == "1" else False if carrier_raw == "0" else None
    speed_raw = read_sysfs_value(root, "speed")
    try:
        speed = int(speed_raw)
        if speed < 0:
            speed = None
    except (TypeError, ValueError):
        speed = None

    return {
        "interface": "end0",
        "available": True,
        "carrier": carrier,
        "operstate": read_sysfs_value(root, "operstate") or "unknown",
        "speed_mbps": speed,
        "duplex": read_sysfs_value(root, "duplex").lower(),
    }


def prune_events(events: deque[float], window_seconds: int, now: float) -> None:
    while events and now - events[0] > window_seconds:
        events.popleft()


def load_previous_events(now: float, max_window_seconds: int = 86400) -> deque[float]:
    state = read_json(STATE_DATA_PATH, {})
    raw = state.get("link_down_events_epoch", []) if isinstance(state, dict) else []
    events: deque[float] = deque(maxlen=200)
    if isinstance(raw, list):
        for value in raw:
            try:
                epoch = float(value)
            except (TypeError, ValueError):
                continue
            if 0 <= now - epoch <= max_window_seconds:
                events.append(epoch)
    return events


def pending_restart(previous_state: dict, boot: dict, boot_id: str) -> tuple[bool, str]:
    prev_pending = bool(previous_state.get("pending_restart", False))
    change_boot_id = str(previous_state.get("change_boot_id") or "")
    if boot.get("write_changed") and boot.get("write_verified"):
        return True, boot_id
    if prev_pending and change_boot_id and change_boot_id != boot_id and boot_id != "unknown":
        return False, ""
    return prev_pending, change_boot_id


def publish_state(state: dict) -> None:
    atomic_json_write(STATE_DATA_PATH, state)
    try:
        atomic_json_write(STATE_HA_PATH, state)
    except OSError as exc:
        log(f"HA mirror write failed: {exc}")


def main() -> int:
    log(f"starting v{APP_VERSION}; EEE ownership is opt-in (default=auto).")
    previous = read_json(STATE_DATA_PATH, {})
    if not isinstance(previous, dict):
        previous = {}

    now = time.time()
    down_events = load_previous_events(now)
    last_carrier = previous.get("carrier")
    last_options_signature = ""
    last_publish = 0.0
    last_boot_check = 0.0
    boot_result = {
        "boot_config_available": False,
        "boot_config_path": "",
        "requested_mode": "auto",
        "configured_off": False,
        "configuration_source": "unavailable",
        "external_eee_off": False,
        "external_eee_on": False,
        "write_changed": False,
        "write_verified": False,
        "backup_path": "",
        "error": "",
    }
    boot_id = current_boot_id()
    pending, change_boot_id = pending_restart(previous, boot_result, boot_id)

    while True:
        cycle_started = time.time()
        options = load_options()
        monitor_enabled = options["ethernet_health_monitor_enabled"]
        window_seconds = int(options["ethernet_flap_window_minutes"]) * 60
        threshold = int(options["ethernet_flap_degraded_threshold"])
        mode = options["ethernet_eee_mode"]
        options_signature = json.dumps({"mode": mode, "monitor": monitor_enabled, "window": window_seconds, "threshold": threshold}, sort_keys=True)

        # Reconcile config.txt on startup/options change and once per minute.
        if options_signature != last_options_signature or cycle_started - last_boot_check >= 60:
            previous = read_json(STATE_DATA_PATH, {})
            if not isinstance(previous, dict):
                previous = {}
            boot_result = update_boot_config(mode)
            boot_id = current_boot_id()
            pending, change_boot_id = pending_restart(previous, boot_result, boot_id)
            last_options_signature = options_signature
            last_boot_check = cycle_started

        link = read_link() if monitor_enabled else {
            "interface": "end0", "available": False, "carrier": None,
            "operstate": "monitor_disabled", "speed_mbps": None, "duplex": "",
        }
        carrier = link.get("carrier")

        if monitor_enabled and carrier is not None and last_carrier is not None and carrier != last_carrier:
            if carrier is False:
                down_events.append(cycle_started)
                log("end0 carrier DOWN detected.")
            else:
                log("end0 carrier UP detected.")
        if carrier is not None:
            last_carrier = carrier

        prune_events(down_events, window_seconds, cycle_started)
        flap_count = len(down_events)

        if not monitor_enabled:
            health = "DISABLED"
        elif not link["available"]:
            health = "UNAVAILABLE"
        elif carrier is False:
            health = "DOWN"
        elif flap_count >= threshold:
            health = "DEGRADED"
        else:
            health = "OK"

        eee_status = "auto"
        if mode == "off":
            if not boot_result.get("configured_off"):
                eee_status = "off_error"
            elif pending:
                eee_status = "off_pending_restart"
            else:
                eee_status = "off_configured"
        elif boot_result.get("external_eee_off"):
            eee_status = "off_external"

        state = {
            "schema": 1,
            "app_version": APP_VERSION,
            "updated": utc_now(),
            "updated_epoch": round(cycle_started, 3),
            "health": health,
            **link,
            "flap_count_window": flap_count,
            "flap_window_minutes": options["ethernet_flap_window_minutes"],
            "degraded_threshold": threshold,
            "link_down_events_epoch": [round(v, 3) for v in down_events],
            "last_link_down_epoch": round(down_events[-1], 3) if down_events else None,
            "eee_requested": mode,
            "eee_status": eee_status,
            "eee_configured_off": bool(boot_result.get("configured_off")),
            "eee_configuration_source": boot_result.get("configuration_source", "unavailable"),
            "eee_external_off": bool(boot_result.get("external_eee_off")),
            "eee_external_on": bool(boot_result.get("external_eee_on")),
            "pending_restart": pending,
            "change_boot_id": change_boot_id,
            "current_boot_id": boot_id,
            "boot_config_available": bool(boot_result.get("boot_config_available")),
            "boot_config_path": boot_result.get("boot_config_path", ""),
            "last_backup_path": boot_result.get("backup_path") or previous.get("last_backup_path", ""),
            "last_error": boot_result.get("error", ""),
        }

        state_changed = any(previous.get(key) != state.get(key) for key in ("health", "carrier", "flap_count_window", "eee_status", "pending_restart", "last_error"))
        if state_changed or cycle_started - last_publish >= 30:
            try:
                publish_state(state)
                previous = state
                last_publish = cycle_started
            except OSError as exc:
                log(f"state write failed: {exc}")

        elapsed = time.time() - cycle_started
        time.sleep(max(0.5, 2.0 - elapsed))


if __name__ == "__main__":
    raise SystemExit(main())
