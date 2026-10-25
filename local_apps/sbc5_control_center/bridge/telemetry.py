from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import json
import os
from pathlib import Path
import shutil
import time

SHARED_TELEMETRY_PATH = Path("/config/sbc5_control_center/telemetry.json")
LEGACY_SHARED_TELEMETRY_PATH = Path("/config/sbc5_fan_manager/telemetry.json")
NAMESPACE_COMPAT_SHARED_TELEMETRY_PATH = Path("/config/rpi5_control_center/telemetry.json")
SHARED_TELEMETRY_MAX_AGE_SECONDS = 45.0
REALTIME_TELEMETRY_PATH = Path("/config/sbc5_control_center/realtime.json")
LEGACY_REALTIME_TELEMETRY_PATH = Path("/config/sbc5_fan_manager/realtime.json")
NAMESPACE_COMPAT_REALTIME_TELEMETRY_PATH = Path("/config/rpi5_control_center/realtime.json")
REALTIME_TELEMETRY_MAX_AGE_SECONDS = 12.0


@dataclass(frozen=True, slots=True)
class TelemetrySnapshot:
    cpu_temperature: float
    fan_rpm: int
    fan_pwm: int
    fan_level: int
    fan_max_level: int
    fan_percent: int
    cooling_status: str
    cooling_problem: bool
    high_temperature: bool
    cpu_frequency_mhz: float | None
    cpu_frequency_min_mhz: float | None
    cpu_frequency_max_mhz: float | None
    cpu_governor: str
    power_supply: str
    power_supply_type: str
    power_supply_official: bool
    power_supply_pd_detected: bool
    power_supply_pd_5a_capable: bool
    power_supply_vid: str
    power_supply_product_vdo: str
    power_max_current_ma: int | None
    power_detection_source: str
    usb_current_limit_ma: int | None
    usb_limit_source: str
    usb_config_override: bool | None
    usb_high_current: bool | None
    usb_over_current_detected: bool | None
    over_current_source: str
    pmic_available: bool
    pmic_source: str
    input_voltage_v: float | None
    pmic_power_w: float | None
    pmic_equivalent_current_a: float | None
    pmic_temperature_c: float | None
    core_current_a: float | None
    core_voltage_v: float | None
    core_power_w: float | None
    pmic_rails: tuple[dict[str, Any], ...]
    usb_device_count: int
    usb_declared_current_ma: int
    usb_devices: tuple[dict[str, Any], ...]
    boot_config_available: bool
    boot_config_device: str
    boot_config_path: str
    boot_config_source: str
    boot_config_sha256: str
    boot_config_entry_count: int
    boot_config_truncated: bool
    boot_config_entries: tuple[dict[str, Any], ...]
    boot_config_includes: tuple[str, ...]
    boot_config_overlays: tuple[dict[str, Any], ...]
    boot_config_dtparams: tuple[dict[str, Any], ...]
    active_config_int: dict[str, str]
    active_config_str: dict[str, str]
    bootloader_config: dict[str, str]
    saved_arm_freq_mhz: float | None
    active_arm_freq_mhz: float | None
    saved_core_freq_mhz: float | None
    active_core_freq_mhz: float | None
    saved_gpu_freq_mhz: float | None
    active_gpu_freq_mhz: float | None
    saved_over_voltage: str
    active_over_voltage: str
    saved_over_voltage_delta: str
    active_over_voltage_delta: str
    saved_usb_max_current_enable: bool | None
    active_usb_max_current_enable: bool | None
    saved_arm_64bit: bool | None
    active_arm_64bit: bool | None
    config_status: str
    config_pending_restart: bool
    kernel_cmdline: str
    kernel_version: str
    architecture: str
    rpi_model: str
    board_revision: str
    hardware_revision: str
    serial_number: str
    network_mac: str
    os_name: str
    os_version: str
    os_pretty_name: str
    firmware_version: str
    firmware_build: str
    bootloader_version: str
    memory_total_mb: float | None
    memory_available_mb: float | None
    memory_used_mb: float | None
    memory_used_percent: float | None
    swap_total_mb: float | None
    swap_used_mb: float | None
    swap_free_mb: float | None
    swap_used_percent: float | None
    rootfs_device: str
    rootfs_mountpoint: str
    rootfs_total_gb: float | None
    rootfs_used_gb: float | None
    rootfs_free_gb: float | None
    rootfs_used_percent: float | None
    load_1m: float | None
    load_5m: float | None
    load_15m: float | None
    uptime_seconds: float | None
    cpu_core_count: int | None
    cpu_core_frequencies_mhz: tuple[float | None, ...]
    cpu_core_usage_percent: tuple[float | None, ...]
    cpu_model: str
    hostname: str
    network_interface: str
    ipv4: str
    network_rx_bytes: int | None
    network_tx_bytes: int | None
    throttled_raw: str
    undervoltage: bool | None
    frequency_capped: bool | None
    throttled: bool | None
    soft_temp_limit: bool | None
    undervoltage_occurred: bool | None
    frequency_capped_occurred: bool | None
    throttled_occurred: bool | None
    soft_temp_limit_occurred: bool | None
    thermal_zones: tuple[dict[str, Any], ...]
    telemetry_source: str
    sample_age_seconds: float | None = field(compare=False)


def _clamp_int(value: object, minimum: int, maximum: int, default: int = 0) -> int:
    try:
        parsed = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))




@dataclass(frozen=True, slots=True)
class RealtimeCoolingSnapshot:
    cpu_temperature: float | None
    fan_rpm: int | None
    fan_pwm: int | None
    fan_percent: int | None
    fan_level: int | None
    fan_max_level: int | None
    sample_age_seconds: float | None = field(compare=False)
    available: bool


def read_realtime_cooling() -> RealtimeCoolingSnapshot:
    """Read cooling telemetry, with a migration fallback to the 1.9.10 path."""
    for path in (REALTIME_TELEMETRY_PATH, NAMESPACE_COMPAT_REALTIME_TELEMETRY_PATH, LEGACY_REALTIME_TELEMETRY_PATH):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            sample_epoch = float(payload.get("sample_epoch", 0))
            age = max(0.0, time.time() - sample_epoch)
            if sample_epoch <= 0 or age > REALTIME_TELEMETRY_MAX_AGE_SECONDS:
                continue
            temp = float(payload["cpu_temperature"])
            if temp < -20 or temp > 150:
                continue
            rpm = _clamp_int(payload.get("fan_rpm"), 0, 100000)
            pwm = _clamp_int(payload.get("fan_pwm"), 0, 255)
            percent = _clamp_int(payload.get("fan_percent", round((pwm / 255) * 100)), 0, 100)
            level = _clamp_int(payload.get("fan_level"), 0, 1000)
            max_level = _clamp_int(payload.get("fan_max_level"), 0, 1000)
            if max_level > 0:
                level = min(level, max_level)
            return RealtimeCoolingSnapshot(
                cpu_temperature=round(temp, 1),
                fan_rpm=rpm,
                fan_pwm=pwm,
                fan_percent=percent,
                fan_level=level,
                fan_max_level=max_level,
                sample_age_seconds=round(age, 2),
                available=True,
            )
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            continue
    return RealtimeCoolingSnapshot(None, None, None, None, None, None, None, False)


def _optional_float(value: object, digits: int = 4) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed < 0:
        return None
    return round(parsed, digits)


def _optional_float_tuple(value: object, *, length: int = 4, digits: int = 1) -> tuple[float | None, ...]:
    seq = value if isinstance(value, (list, tuple)) else ()
    result: list[float | None] = []
    for idx in range(length):
        item = seq[idx] if idx < len(seq) else None
        result.append(_optional_float(item, digits))
    return tuple(result)


def _optional_int(value: object) -> int | None:
    try:
        parsed = int(float(value))
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _optional_bool(value: object) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return None


def _object_tuple(value: object) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        return ()
    result: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            result.append(dict(item))
    return tuple(result)


def _object_dict(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(k): str(v) for k, v in value.items()}


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value)


def _cooling_status(temp: float, rpm: int, level: int, max_level: int) -> str:
    if temp >= 82:
        return "Krytyczna temperatura"
    if level <= 0 or rpm <= 0:
        return "Chłodzenie pasywne"
    if max_level <= 0:
        return "Chłodzenie aktywne"
    relative = level * 100 / max_level
    if relative <= 20:
        return "Bardzo niskie chłodzenie"
    if relative <= 40:
        return "Niskie chłodzenie"
    if relative <= 67:
        return "Średnie chłodzenie"
    if relative <= 87:
        return "Wysokie chłodzenie"
    return "Maksymalne chłodzenie"


def _read_local_system_metrics() -> dict[str, object]:
    metrics: dict[str, object] = {
        "memory_total_mb": None,
        "memory_available_mb": None,
        "memory_used_mb": None,
        "memory_used_percent": None,
        "swap_total_mb": None,
        "swap_used_mb": None,
        "swap_free_mb": None,
        "swap_used_percent": None,
        "rootfs_device": "",
        "rootfs_mountpoint": "/",
        "rootfs_total_gb": None,
        "rootfs_used_gb": None,
        "rootfs_free_gb": None,
        "rootfs_used_percent": None,
        "load_1m": None,
        "load_5m": None,
        "load_15m": None,
        "uptime_seconds": None,
        "cpu_core_count": os.cpu_count(),
        "cpu_model": "",
        "hostname": "",
        "network_interface": "",
        "ipv4": "",
        "network_rx_bytes": None,
        "network_tx_bytes": None,
        "throttled_raw": "",
        "undervoltage": None,
        "frequency_capped": None,
        "throttled": None,
        "soft_temp_limit": None,
        "undervoltage_occurred": None,
        "frequency_capped_occurred": None,
        "throttled_occurred": None,
        "soft_temp_limit_occurred": None,
        "thermal_zones": [],
    }
    try:
        meminfo: dict[str, int] = {}
        with open("/proc/meminfo", "r", encoding="utf-8") as fh:
            for line in fh:
                if ":" not in line:
                    continue
                key, raw = line.split(":", 1)
                num = raw.strip().split()[0]
                if num.isdigit():
                    meminfo[key] = int(num)
        mem_total = meminfo.get("MemTotal")
        mem_available = meminfo.get("MemAvailable")
        if mem_total:
            metrics["memory_total_mb"] = round(mem_total / 1024, 1)
            if mem_available is not None:
                used = mem_total - mem_available
                metrics["memory_available_mb"] = round(mem_available / 1024, 1)
                metrics["memory_used_mb"] = round(used / 1024, 1)
                metrics["memory_used_percent"] = round((used * 100.0) / mem_total, 1)
        swap_total = meminfo.get("SwapTotal")
        swap_free = meminfo.get("SwapFree")
        if swap_total and swap_total > 0:
            used = swap_total - (swap_free or 0)
            metrics["swap_total_mb"] = round(swap_total / 1024, 1)
            metrics["swap_used_mb"] = round(used / 1024, 1)
            metrics["swap_free_mb"] = round((swap_free or 0) / 1024, 1)
            metrics["swap_used_percent"] = round((used * 100.0) / swap_total, 1)
    except OSError:
        pass
    try:
        total, used, free = shutil.disk_usage("/")
        metrics["rootfs_total_gb"] = round(total / (1024**3), 2)
        metrics["rootfs_used_gb"] = round(used / (1024**3), 2)
        metrics["rootfs_free_gb"] = round(free / (1024**3), 2)
        if total:
            metrics["rootfs_used_percent"] = round((used * 100.0) / total, 1)
    except OSError:
        pass
    try:
        load_1m, load_5m, load_15m = os.getloadavg()
        metrics["load_1m"] = round(load_1m, 2)
        metrics["load_5m"] = round(load_5m, 2)
        metrics["load_15m"] = round(load_15m, 2)
    except OSError:
        pass
    try:
        with open("/proc/uptime", "r", encoding="utf-8") as fh:
            metrics["uptime_seconds"] = round(float(fh.read().split()[0]), 1)
    except (OSError, ValueError, IndexError):
        pass
    try:
        metrics["hostname"] = os.uname().nodename
    except OSError:
        pass
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("Model") or line.startswith("model name"):
                    metrics["cpu_model"] = line.split(":", 1)[1].strip()
                    break
    except (OSError, IndexError):
        pass
    try:
        zones = []
        for zone in Path("/sys/class/thermal").glob("thermal_zone*"):
            temp_path = zone / "temp"
            if not temp_path.is_file():
                continue
            raw = float(temp_path.read_text(encoding="utf-8").strip())
            temp_c = raw / 1000.0 if abs(raw) > 1000 else raw
            type_path = zone / "type"
            ztype = type_path.read_text(encoding="utf-8").strip() if type_path.is_file() else zone.name
            zones.append({"type": ztype, "temp_c": round(temp_c, 1)})
        metrics["thermal_zones"] = zones
    except (OSError, ValueError):
        pass
    return metrics


def build_snapshot(
    temp: object,
    rpm: object,
    pwm: object,
    level: object,
    max_level: object,
    *,
    source: str,
    age: float | None = None,
    cpu_frequency_mhz: object = None,
    cpu_frequency_min_mhz: object = None,
    cpu_frequency_max_mhz: object = None,
    cpu_governor: object = "",
    power_supply: object = "Nieznany",
    power_supply_type: object = "unknown",
    power_supply_official: object = False,
    power_supply_pd_detected: object = False,
    power_supply_pd_5a_capable: object = False,
    power_supply_vid: object = "",
    power_supply_product_vdo: object = "",
    power_max_current_ma: object = None,
    power_detection_source: object = "unavailable",
    usb_current_limit_ma: object = None,
    usb_limit_source: object = "unavailable",
    usb_config_override: object = None,
    usb_high_current: object = None,
    usb_over_current_detected: object = None,
    over_current_source: object = "unavailable",
    pmic_available: object = False,
    pmic_source: object = "unavailable",
    input_voltage_v: object = None,
    pmic_power_w: object = None,
    pmic_equivalent_current_a: object = None,
    pmic_temperature_c: object = None,
    core_current_a: object = None,
    core_voltage_v: object = None,
    core_power_w: object = None,
    pmic_rails: object = None,
    usb_device_count: object = 0,
    usb_declared_current_ma: object = 0,
    usb_devices: object = None,
    boot_config_available: object = False,
    boot_config_device: object = "",
    boot_config_path: object = "",
    boot_config_source: object = "",
    boot_config_sha256: object = "",
    boot_config_entry_count: object = 0,
    boot_config_truncated: object = False,
    boot_config_entries: object = None,
    boot_config_includes: object = None,
    boot_config_overlays: object = None,
    boot_config_dtparams: object = None,
    active_config_int: object = None,
    active_config_str: object = None,
    bootloader_config: object = None,
    saved_arm_freq_mhz: object = None,
    active_arm_freq_mhz: object = None,
    saved_core_freq_mhz: object = None,
    active_core_freq_mhz: object = None,
    saved_gpu_freq_mhz: object = None,
    active_gpu_freq_mhz: object = None,
    saved_over_voltage: object = "",
    active_over_voltage: object = "",
    saved_over_voltage_delta: object = "",
    active_over_voltage_delta: object = "",
    saved_usb_max_current_enable: object = None,
    active_usb_max_current_enable: object = None,
    saved_arm_64bit: object = None,
    active_arm_64bit: object = None,
    config_status: object = "Niedostępna",
    config_pending_restart: object = False,
    kernel_cmdline: object = "",
    kernel_version: object = "",
    architecture: object = "",
    rpi_model: object = "",
    board_revision: object = "",
    hardware_revision: object = "",
    serial_number: object = "",
    network_mac: object = "",
    os_name: object = "",
    os_version: object = "",
    os_pretty_name: object = "",
    firmware_version: object = "",
    firmware_build: object = "",
    bootloader_version: object = "",
    memory_total_mb: object = None,
    memory_available_mb: object = None,
    memory_used_mb: object = None,
    memory_used_percent: object = None,
    swap_total_mb: object = None,
    swap_used_mb: object = None,
    swap_free_mb: object = None,
    swap_used_percent: object = None,
    rootfs_device: object = "",
    rootfs_mountpoint: object = "/",
    rootfs_total_gb: object = None,
    rootfs_used_gb: object = None,
    rootfs_free_gb: object = None,
    rootfs_used_percent: object = None,
    load_1m: object = None,
    load_5m: object = None,
    load_15m: object = None,
    uptime_seconds: object = None,
    cpu_core_count: object = None,
    cpu_core_frequencies_mhz: object = None,
    cpu_core_usage_percent: object = None,
    cpu_model: object = "",
    hostname: object = "",
    network_interface: object = "",
    ipv4: object = "",
    network_rx_bytes: object = None,
    network_tx_bytes: object = None,
    throttled_raw: object = "",
    undervoltage: object = None,
    frequency_capped: object = None,
    throttled: object = None,
    soft_temp_limit: object = None,
    undervoltage_occurred: object = None,
    frequency_capped_occurred: object = None,
    throttled_occurred: object = None,
    soft_temp_limit_occurred: object = None,
    thermal_zones: object = None,
) -> TelemetrySnapshot:
    try:
        temp_f = float(temp)
    except (TypeError, ValueError):
        temp_f = 0.0
    rpm_i = _clamp_int(rpm, 0, 100000)
    pwm_i = _clamp_int(pwm, 0, 255)
    level_i = _clamp_int(level, 0, 1000)
    max_level_i = _clamp_int(max_level, 0, 1000)
    if max_level_i > 0:
        level_i = min(level_i, max_level_i)

    percent = max(0, min(100, round((pwm_i / 255) * 100)))
    return TelemetrySnapshot(
        cpu_temperature=round(temp_f, 1),
        fan_rpm=rpm_i,
        fan_pwm=pwm_i,
        fan_level=level_i,
        fan_max_level=max_level_i,
        fan_percent=percent,
        cooling_status=_cooling_status(temp_f, rpm_i, level_i, max_level_i),
        cooling_problem=pwm_i >= 60 and rpm_i < 100,
        high_temperature=temp_f >= 75,
        cpu_frequency_mhz=_optional_float(cpu_frequency_mhz, 1),
        cpu_frequency_min_mhz=_optional_float(cpu_frequency_min_mhz, 1),
        cpu_frequency_max_mhz=_optional_float(cpu_frequency_max_mhz, 1),
        cpu_governor=str(cpu_governor or ""),
        power_supply=str(power_supply or "Nieznany"),
        power_supply_type=str(power_supply_type or "unknown"),
        power_supply_official=bool(power_supply_official),
        power_supply_pd_detected=bool(power_supply_pd_detected),
        power_supply_pd_5a_capable=bool(power_supply_pd_5a_capable),
        power_supply_vid=str(power_supply_vid or ""),
        power_supply_product_vdo=str(power_supply_product_vdo or ""),
        power_max_current_ma=_optional_int(power_max_current_ma),
        power_detection_source=str(power_detection_source or "unavailable"),
        usb_current_limit_ma=_optional_int(usb_current_limit_ma),
        usb_limit_source=str(usb_limit_source or "unavailable"),
        usb_config_override=_optional_bool(usb_config_override),
        usb_high_current=_optional_bool(usb_high_current),
        usb_over_current_detected=_optional_bool(usb_over_current_detected),
        over_current_source=str(over_current_source or "unavailable"),
        pmic_available=bool(pmic_available),
        pmic_source=str(pmic_source or "unavailable"),
        input_voltage_v=_optional_float(input_voltage_v),
        pmic_power_w=_optional_float(pmic_power_w, 3),
        pmic_equivalent_current_a=_optional_float(pmic_equivalent_current_a, 3),
        pmic_temperature_c=_optional_float(pmic_temperature_c, 1),
        core_current_a=_optional_float(core_current_a),
        core_voltage_v=_optional_float(core_voltage_v),
        core_power_w=_optional_float(core_power_w, 3),
        pmic_rails=_object_tuple(pmic_rails),
        usb_device_count=_clamp_int(usb_device_count, 0, 128),
        usb_declared_current_ma=_clamp_int(usb_declared_current_ma, 0, 100000),
        usb_devices=_object_tuple(usb_devices),
        boot_config_available=bool(boot_config_available),
        boot_config_device=str(boot_config_device or ""),
        boot_config_path=str(boot_config_path or ""),
        boot_config_source=str(boot_config_source or ""),
        boot_config_sha256=str(boot_config_sha256 or ""),
        boot_config_entry_count=_clamp_int(boot_config_entry_count, 0, 10000),
        boot_config_truncated=bool(boot_config_truncated),
        boot_config_entries=_object_tuple(boot_config_entries),
        boot_config_includes=_string_tuple(boot_config_includes),
        boot_config_overlays=_object_tuple(boot_config_overlays),
        boot_config_dtparams=_object_tuple(boot_config_dtparams),
        active_config_int=_object_dict(active_config_int),
        active_config_str=_object_dict(active_config_str),
        bootloader_config=_object_dict(bootloader_config),
        saved_arm_freq_mhz=_optional_float(saved_arm_freq_mhz, 1),
        active_arm_freq_mhz=_optional_float(active_arm_freq_mhz, 1),
        saved_core_freq_mhz=_optional_float(saved_core_freq_mhz, 1),
        active_core_freq_mhz=_optional_float(active_core_freq_mhz, 1),
        saved_gpu_freq_mhz=_optional_float(saved_gpu_freq_mhz, 1),
        active_gpu_freq_mhz=_optional_float(active_gpu_freq_mhz, 1),
        saved_over_voltage=str(saved_over_voltage or ""),
        active_over_voltage=str(active_over_voltage or ""),
        saved_over_voltage_delta=str(saved_over_voltage_delta or ""),
        active_over_voltage_delta=str(active_over_voltage_delta or ""),
        saved_usb_max_current_enable=_optional_bool(saved_usb_max_current_enable),
        active_usb_max_current_enable=_optional_bool(active_usb_max_current_enable),
        saved_arm_64bit=_optional_bool(saved_arm_64bit),
        active_arm_64bit=_optional_bool(active_arm_64bit),
        config_status=str(config_status or "Niedostępna"),
        config_pending_restart=bool(config_pending_restart),
        kernel_cmdline=str(kernel_cmdline or ""),
        kernel_version=str(kernel_version or ""),
        architecture=str(architecture or ""),
        rpi_model=str(rpi_model or ""),
        board_revision=str(board_revision or ""),
        hardware_revision=str(hardware_revision or ""),
        serial_number=str(serial_number or ""),
        network_mac=str(network_mac or "").lower(),
        os_name=str(os_name or ""),
        os_version=str(os_version or ""),
        os_pretty_name=str(os_pretty_name or ""),
        firmware_version=str(firmware_version or ""),
        firmware_build=str(firmware_build or ""),
        bootloader_version=str(bootloader_version or ""),
        memory_total_mb=_optional_float(memory_total_mb, 1),
        memory_available_mb=_optional_float(memory_available_mb, 1),
        memory_used_mb=_optional_float(memory_used_mb, 1),
        memory_used_percent=_optional_float(memory_used_percent, 1),
        swap_total_mb=_optional_float(swap_total_mb, 1),
        swap_used_mb=_optional_float(swap_used_mb, 1),
        swap_free_mb=_optional_float(swap_free_mb, 1),
        swap_used_percent=_optional_float(swap_used_percent, 1),
        rootfs_device=str(rootfs_device or ""),
        rootfs_mountpoint=str(rootfs_mountpoint or "/"),
        rootfs_total_gb=_optional_float(rootfs_total_gb, 2),
        rootfs_used_gb=_optional_float(rootfs_used_gb, 2),
        rootfs_free_gb=_optional_float(rootfs_free_gb, 2),
        rootfs_used_percent=_optional_float(rootfs_used_percent, 1),
        load_1m=_optional_float(load_1m, 2),
        load_5m=_optional_float(load_5m, 2),
        load_15m=_optional_float(load_15m, 2),
        uptime_seconds=_optional_float(uptime_seconds, 1),
        cpu_core_count=_optional_int(cpu_core_count),
        cpu_core_frequencies_mhz=_optional_float_tuple(cpu_core_frequencies_mhz, length=4, digits=1),
        cpu_core_usage_percent=_optional_float_tuple(cpu_core_usage_percent, length=4, digits=1),
        cpu_model=str(cpu_model or ""),
        hostname=str(hostname or ""),
        network_interface=str(network_interface or ""),
        ipv4=str(ipv4 or ""),
        network_rx_bytes=_optional_int(network_rx_bytes),
        network_tx_bytes=_optional_int(network_tx_bytes),
        throttled_raw=str(throttled_raw or ""),
        undervoltage=_optional_bool(undervoltage),
        frequency_capped=_optional_bool(frequency_capped),
        throttled=_optional_bool(throttled),
        soft_temp_limit=_optional_bool(soft_temp_limit),
        undervoltage_occurred=_optional_bool(undervoltage_occurred),
        frequency_capped_occurred=_optional_bool(frequency_capped_occurred),
        throttled_occurred=_optional_bool(throttled_occurred),
        soft_temp_limit_occurred=_optional_bool(soft_temp_limit_occurred),
        thermal_zones=_object_tuple(thermal_zones),
        telemetry_source=source,
        sample_age_seconds=round(age, 1) if age is not None else None,
    )


def _snapshot_from_payload(payload: dict[str, Any], *, source: str, age: float) -> TelemetrySnapshot:
    temp = float(payload["cpu_temperature"])
    if temp < -20 or temp > 150:
        raise ValueError("invalid CPU temperature")
    local = _read_local_system_metrics()
    return build_snapshot(
        temp,
        payload["fan_rpm"],
        payload["fan_pwm"],
        payload["fan_level"],
        payload["fan_max_level"],
        source=source,
        age=age,
        cpu_frequency_mhz=payload.get("cpu_frequency_mhz"),
        cpu_frequency_min_mhz=payload.get("cpu_frequency_min_mhz"),
        cpu_frequency_max_mhz=payload.get("cpu_frequency_max_mhz"),
        cpu_governor=payload.get("cpu_governor", ""),
        power_supply=payload.get("power_supply", "Nieznany"),
        power_supply_type=payload.get("power_supply_type", "unknown"),
        power_supply_official=payload.get("power_supply_official", False),
        power_supply_pd_detected=payload.get("power_supply_pd_detected", False),
        power_supply_pd_5a_capable=payload.get("power_supply_pd_5a_capable", False),
        power_supply_vid=payload.get("power_supply_vid", ""),
        power_supply_product_vdo=payload.get("power_supply_product_vdo", ""),
        power_max_current_ma=payload.get("power_max_current_ma"),
        power_detection_source=payload.get("power_detection_source", "unavailable"),
        usb_current_limit_ma=payload.get("usb_current_limit_ma"),
        usb_limit_source=payload.get("usb_limit_source", "unavailable"),
        usb_config_override=payload.get("usb_config_override"),
        usb_high_current=payload.get("usb_high_current"),
        usb_over_current_detected=payload.get("usb_over_current_detected"),
        over_current_source=payload.get("over_current_source", "unavailable"),
        pmic_available=payload.get("pmic_available", False),
        pmic_source=payload.get("pmic_source", "unavailable"),
        input_voltage_v=payload.get("input_voltage_v"),
        pmic_power_w=payload.get("pmic_power_w"),
        pmic_equivalent_current_a=payload.get("pmic_equivalent_current_a"),
        pmic_temperature_c=payload.get("pmic_temperature_c"),
        core_current_a=payload.get("core_current_a"),
        core_voltage_v=payload.get("core_voltage_v"),
        core_power_w=payload.get("core_power_w"),
        pmic_rails=payload.get("pmic_rails", []),
        usb_device_count=payload.get("usb_device_count", 0),
        usb_declared_current_ma=payload.get("usb_declared_current_ma", 0),
        usb_devices=payload.get("usb_devices", []),
        boot_config_available=payload.get("boot_config_available", False),
        boot_config_device=payload.get("boot_config_device", ""),
        boot_config_path=payload.get("boot_config_path", ""),
        boot_config_source=payload.get("boot_config_source", ""),
        boot_config_sha256=payload.get("boot_config_sha256", ""),
        boot_config_entry_count=payload.get("boot_config_entry_count", 0),
        boot_config_truncated=payload.get("boot_config_truncated", False),
        boot_config_entries=payload.get("boot_config_entries", []),
        boot_config_includes=payload.get("boot_config_includes", []),
        boot_config_overlays=payload.get("boot_config_overlays", []),
        boot_config_dtparams=payload.get("boot_config_dtparams", []),
        active_config_int=payload.get("active_config_int", {}),
        active_config_str=payload.get("active_config_str", {}),
        bootloader_config=payload.get("bootloader_config", {}),
        saved_arm_freq_mhz=payload.get("saved_arm_freq_mhz"),
        active_arm_freq_mhz=payload.get("active_arm_freq_mhz"),
        saved_core_freq_mhz=payload.get("saved_core_freq_mhz"),
        active_core_freq_mhz=payload.get("active_core_freq_mhz"),
        saved_gpu_freq_mhz=payload.get("saved_gpu_freq_mhz"),
        active_gpu_freq_mhz=payload.get("active_gpu_freq_mhz"),
        saved_over_voltage=payload.get("saved_over_voltage", ""),
        active_over_voltage=payload.get("active_over_voltage", ""),
        saved_over_voltage_delta=payload.get("saved_over_voltage_delta", ""),
        active_over_voltage_delta=payload.get("active_over_voltage_delta", ""),
        saved_usb_max_current_enable=payload.get("saved_usb_max_current_enable"),
        active_usb_max_current_enable=payload.get("active_usb_max_current_enable"),
        saved_arm_64bit=payload.get("saved_arm_64bit"),
        active_arm_64bit=payload.get("active_arm_64bit"),
        config_status=payload.get("config_status", "Niedostępna"),
        config_pending_restart=payload.get("config_pending_restart", False),
        kernel_cmdline=payload.get("kernel_cmdline", ""),
        kernel_version=payload.get("kernel_version", ""),
        architecture=payload.get("architecture", ""),
        rpi_model=payload.get("rpi_model", ""),
        board_revision=payload.get("board_revision", ""),
        hardware_revision=payload.get("hardware_revision", ""),
        serial_number=payload.get("serial_number", ""),
        network_mac=payload.get("network_mac", ""),
        os_name=payload.get("os_name", ""),
        os_version=payload.get("os_version", ""),
        os_pretty_name=payload.get("os_pretty_name", ""),
        firmware_version=payload.get("firmware_version", ""),
        firmware_build=payload.get("firmware_build", ""),
        bootloader_version=payload.get("bootloader_version", ""),
        memory_total_mb=payload.get("memory_total_mb", local.get("memory_total_mb")),
        memory_available_mb=payload.get("memory_available_mb", local.get("memory_available_mb")),
        memory_used_mb=payload.get("memory_used_mb", local.get("memory_used_mb")),
        memory_used_percent=payload.get("memory_used_percent", local.get("memory_used_percent")),
        swap_total_mb=payload.get("swap_total_mb", local.get("swap_total_mb")),
        swap_used_mb=payload.get("swap_used_mb", local.get("swap_used_mb")),
        swap_free_mb=payload.get("swap_free_mb", local.get("swap_free_mb")),
        swap_used_percent=payload.get("swap_used_percent", local.get("swap_used_percent")),
        rootfs_device=payload.get("rootfs_device", local.get("rootfs_device", "")),
        rootfs_mountpoint=payload.get("rootfs_mountpoint", local.get("rootfs_mountpoint", "/")),
        rootfs_total_gb=payload.get("rootfs_total_gb", local.get("rootfs_total_gb")),
        rootfs_used_gb=payload.get("rootfs_used_gb", local.get("rootfs_used_gb")),
        rootfs_free_gb=payload.get("rootfs_free_gb", local.get("rootfs_free_gb")),
        rootfs_used_percent=payload.get("rootfs_used_percent", local.get("rootfs_used_percent")),
        load_1m=payload.get("load_1m", local.get("load_1m")),
        load_5m=payload.get("load_5m", local.get("load_5m")),
        load_15m=payload.get("load_15m", local.get("load_15m")),
        uptime_seconds=payload.get("uptime_seconds", local.get("uptime_seconds")),
        cpu_core_count=payload.get("cpu_core_count", local.get("cpu_core_count")),
        cpu_core_frequencies_mhz=payload.get("cpu_core_frequencies_mhz", []),
        cpu_core_usage_percent=payload.get("cpu_core_usage_percent", []),
        cpu_model=payload.get("cpu_model", local.get("cpu_model", "")),
        hostname=payload.get("hostname", local.get("hostname", "")),
        network_interface=payload.get("network_interface", local.get("network_interface", "")),
        ipv4=payload.get("ipv4", local.get("ipv4", "")),
        network_rx_bytes=payload.get("network_rx_bytes", local.get("network_rx_bytes")),
        network_tx_bytes=payload.get("network_tx_bytes", local.get("network_tx_bytes")),
        throttled_raw=payload.get("throttled_raw", local.get("throttled_raw", "")),
        undervoltage=payload.get("undervoltage", local.get("undervoltage")),
        frequency_capped=payload.get("frequency_capped", local.get("frequency_capped")),
        throttled=payload.get("throttled", local.get("throttled")),
        soft_temp_limit=payload.get("soft_temp_limit", local.get("soft_temp_limit")),
        undervoltage_occurred=payload.get("undervoltage_occurred", local.get("undervoltage_occurred")),
        frequency_capped_occurred=payload.get("frequency_capped_occurred", local.get("frequency_capped_occurred")),
        throttled_occurred=payload.get("throttled_occurred", local.get("throttled_occurred")),
        soft_temp_limit_occurred=payload.get("soft_temp_limit_occurred", local.get("soft_temp_limit_occurred")),
        thermal_zones=payload.get("thermal_zones", local.get("thermal_zones", [])),
    )


def _read_shared_telemetry() -> TelemetrySnapshot | None:
    for path, source in (
        (SHARED_TELEMETRY_PATH, "app_shared_json"),
        (NAMESPACE_COMPAT_SHARED_TELEMETRY_PATH, "app_shared_json_namespace_compat"),
        (LEGACY_SHARED_TELEMETRY_PATH, "app_shared_json_legacy_1_9_10"),
    ):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            sample_epoch = float(payload.get("sample_epoch", 0))
            age = max(0.0, time.time() - sample_epoch)
            if sample_epoch <= 0 or age > SHARED_TELEMETRY_MAX_AGE_SECONDS:
                continue
            return _snapshot_from_payload(payload, source=source, age=age)
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            continue
    return None


def read_shared_telemetry() -> TelemetrySnapshot | None:
    """Read only the shared app snapshot without local-system fallback."""
    return _read_shared_telemetry()


def read_telemetry() -> TelemetrySnapshot:
    """Read authoritative host telemetry written by the Control Center app."""
    shared = _read_shared_telemetry()
    if shared is not None:
        return shared
    local = _read_local_system_metrics()
    return build_snapshot(
        0,
        0,
        0,
        0,
        0,
        source="waiting_for_host_telemetry",
        memory_total_mb=local.get("memory_total_mb"),
        memory_available_mb=local.get("memory_available_mb"),
        memory_used_mb=local.get("memory_used_mb"),
        memory_used_percent=local.get("memory_used_percent"),
        swap_total_mb=local.get("swap_total_mb"),
        swap_used_mb=local.get("swap_used_mb"),
        swap_free_mb=local.get("swap_free_mb"),
        swap_used_percent=local.get("swap_used_percent"),
        rootfs_device=local.get("rootfs_device", ""),
        rootfs_mountpoint=local.get("rootfs_mountpoint", "/"),
        rootfs_total_gb=local.get("rootfs_total_gb"),
        rootfs_used_gb=local.get("rootfs_used_gb"),
        rootfs_free_gb=local.get("rootfs_free_gb"),
        rootfs_used_percent=local.get("rootfs_used_percent"),
        load_1m=local.get("load_1m"),
        load_5m=local.get("load_5m"),
        load_15m=local.get("load_15m"),
        uptime_seconds=local.get("uptime_seconds"),
        cpu_core_count=local.get("cpu_core_count"),
        cpu_model=local.get("cpu_model", ""),
        hostname=local.get("hostname", ""),
        network_interface=local.get("network_interface", ""),
        ipv4=local.get("ipv4", ""),
        network_rx_bytes=local.get("network_rx_bytes"),
        network_tx_bytes=local.get("network_tx_bytes"),
        throttled_raw=local.get("throttled_raw", ""),
        undervoltage=local.get("undervoltage"),
        frequency_capped=local.get("frequency_capped"),
        throttled=local.get("throttled"),
        soft_temp_limit=local.get("soft_temp_limit"),
        undervoltage_occurred=local.get("undervoltage_occurred"),
        frequency_capped_occurred=local.get("frequency_capped_occurred"),
        throttled_occurred=local.get("throttled_occurred"),
        soft_temp_limit_occurred=local.get("soft_temp_limit_occurred"),
        thermal_zones=local.get("thermal_zones", []),
    )
