from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from datetime import timedelta
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import APP_VERSION, DOMAIN
from .telemetry import RealtimeCoolingSnapshot, TelemetrySnapshot, build_snapshot, read_realtime_cooling, read_shared_telemetry, read_telemetry

_LOGGER = logging.getLogger(__name__)
HOST_TELEMETRY_ENTITY = "sensor.sbc5_control_center_host_telemetry"
LEGACY_HOST_TELEMETRY_ENTITY = "sensor.rpi5_control_center_host_telemetry"
HOST_TELEMETRY_MAX_AGE_SECONDS = 30.0
HOST_TELEMETRY_ENTITIES = tuple(dict.fromkeys((
    HOST_TELEMETRY_ENTITY,
    LEGACY_HOST_TELEMETRY_ENTITY,
    "sensor.sbc5_control_center_host_telemetry",
    "sensor.rpi5_control_center_host_telemetry",
    "sensor.rpi5_fan_manager_host_telemetry",
)))


@dataclass(frozen=True, slots=True)
class AppUpdateInfo:
    state: str
    installed_version: str
    latest_version: str
    source: str
    repository: str
    release_url: str
    download_url: str
    changelog_url: str
    restart_required: str
    release_date: str
    summary: str
    local_package_file: str
    local_install_supported: bool
    runtime_app_slug: str
    update_scope: str
    card_ui_installed_version: str
    card_ui_latest_version: str


@dataclass(frozen=True, slots=True)
class SBC5CoordinatorData:
    telemetry: TelemetrySnapshot
    app_update: AppUpdateInfo
    thermal_predictor: dict[str, Any]
    ethernet_health: dict[str, Any]


def _read_ethernet_health(hass: HomeAssistant) -> dict[str, Any]:
    path = Path(hass.config.path("sbc5_control_center/ethernet_health.json"))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def _telemetry_from_host_relay(hass: HomeAssistant) -> TelemetrySnapshot | None:
    """Read canonical host relay, falling back to the pre-1.9.11 entity during migration."""
    for entity_id in HOST_TELEMETRY_ENTITIES:
        state = hass.states.get(entity_id)
        if state is None:
            continue
        attrs = state.attributes
        try:
            sample_epoch = float(attrs.get("sample_epoch", 0))
            age = max(0.0, time.time() - sample_epoch)
            if sample_epoch <= 0 or age > HOST_TELEMETRY_MAX_AGE_SECONDS:
                continue
            temp = float(attrs["cpu_temperature"])
            if temp < -20 or temp > 150:
                continue
            fan_pwm = attrs.get("fan_pwm", attrs.get("fan_pwm_raw"))
            if fan_pwm is None:
                continue
            return build_snapshot(
                temp, attrs["fan_rpm"], fan_pwm, attrs["fan_level"], attrs["fan_max_level"],
                source="addon_host_relay" if entity_id == HOST_TELEMETRY_ENTITY else "addon_host_relay_namespace_compat",
                age=age,
                cpu_frequency_mhz=attrs.get("cpu_frequency_mhz"), cpu_frequency_min_mhz=attrs.get("cpu_frequency_min_mhz"),
                cpu_frequency_max_mhz=attrs.get("cpu_frequency_max_mhz"), cpu_governor=attrs.get("cpu_governor", ""),
                cpu_core_frequencies_mhz=attrs.get("cpu_core_frequencies_mhz", []), cpu_core_usage_percent=attrs.get("cpu_core_usage_percent", []),
                power_supply=attrs.get("power_supply", "Nieznany"), power_supply_type=attrs.get("power_supply_type", "unknown"),
                power_supply_official=attrs.get("power_supply_official", False), power_supply_pd_detected=attrs.get("power_supply_pd_detected", False),
                power_supply_pd_5a_capable=attrs.get("power_supply_pd_5a_capable", False), power_supply_vid=attrs.get("power_supply_vid", ""),
                power_supply_product_vdo=attrs.get("power_supply_product_vdo", ""), power_max_current_ma=attrs.get("power_max_current_ma"),
                power_detection_source=attrs.get("power_detection_source", "unavailable"), usb_current_limit_ma=attrs.get("usb_current_limit_ma"),
                usb_limit_source=attrs.get("usb_limit_source", "unavailable"), usb_config_override=attrs.get("usb_config_override"),
                usb_high_current=attrs.get("usb_high_current"), usb_over_current_detected=attrs.get("usb_over_current_detected"),
                over_current_source=attrs.get("over_current_source", "unavailable"), pmic_available=attrs.get("pmic_available", False),
                pmic_source=attrs.get("pmic_source", "unavailable"), input_voltage_v=attrs.get("input_voltage_v"), pmic_power_w=attrs.get("pmic_power_w"),
                pmic_equivalent_current_a=attrs.get("pmic_equivalent_current_a"), pmic_temperature_c=attrs.get("pmic_temperature_c"),
                core_current_a=attrs.get("core_current_a"), core_voltage_v=attrs.get("core_voltage_v"), core_power_w=attrs.get("core_power_w"),
                pmic_rails=attrs.get("pmic_rails", []), usb_device_count=attrs.get("usb_device_count", 0),
                usb_declared_current_ma=attrs.get("usb_declared_current_ma", 0), usb_devices=attrs.get("usb_devices", []),
                boot_config_available=attrs.get("boot_config_available", False), boot_config_device=attrs.get("boot_config_device", ""),
                boot_config_path=attrs.get("boot_config_path", ""), boot_config_source=attrs.get("boot_config_source", ""),
                boot_config_sha256=attrs.get("boot_config_sha256", ""), boot_config_entry_count=attrs.get("boot_config_entry_count", 0),
                boot_config_truncated=attrs.get("boot_config_truncated", False), boot_config_entries=attrs.get("boot_config_entries", []),
                boot_config_includes=attrs.get("boot_config_includes", []), boot_config_overlays=attrs.get("boot_config_overlays", []),
                boot_config_dtparams=attrs.get("boot_config_dtparams", []), active_config_int=attrs.get("active_config_int", {}),
                active_config_str=attrs.get("active_config_str", {}), bootloader_config=attrs.get("bootloader_config", {}),
                saved_arm_freq_mhz=attrs.get("saved_arm_freq_mhz"), active_arm_freq_mhz=attrs.get("active_arm_freq_mhz"),
                saved_core_freq_mhz=attrs.get("saved_core_freq_mhz"), active_core_freq_mhz=attrs.get("active_core_freq_mhz"),
                saved_gpu_freq_mhz=attrs.get("saved_gpu_freq_mhz"), active_gpu_freq_mhz=attrs.get("active_gpu_freq_mhz"),
                saved_over_voltage=attrs.get("saved_over_voltage", ""), active_over_voltage=attrs.get("active_over_voltage", ""),
                saved_over_voltage_delta=attrs.get("saved_over_voltage_delta", ""), active_over_voltage_delta=attrs.get("active_over_voltage_delta", ""),
                saved_usb_max_current_enable=attrs.get("saved_usb_max_current_enable"), active_usb_max_current_enable=attrs.get("active_usb_max_current_enable"),
                saved_arm_64bit=attrs.get("saved_arm_64bit"), active_arm_64bit=attrs.get("active_arm_64bit"),
                config_status=attrs.get("config_status", "Niedostępna"), config_pending_restart=attrs.get("config_pending_restart", False),
                kernel_cmdline=attrs.get("kernel_cmdline", ""), kernel_version=attrs.get("kernel_version", ""), architecture=attrs.get("architecture", ""),
                rpi_model=attrs.get("rpi_model", ""), board_revision=attrs.get("board_revision", ""),
                hardware_revision=attrs.get("hardware_revision", ""), serial_number=attrs.get("serial_number", ""),
                network_mac=attrs.get("network_mac", ""), os_name=attrs.get("os_name", ""), os_version=attrs.get("os_version", ""),
                os_pretty_name=attrs.get("os_pretty_name", ""), firmware_version=attrs.get("firmware_version", ""),
                firmware_build=attrs.get("firmware_build", ""), bootloader_version=attrs.get("bootloader_version", ""),
                memory_total_mb=attrs.get("memory_total_mb"), memory_available_mb=attrs.get("memory_available_mb"),
                memory_used_mb=attrs.get("memory_used_mb"), memory_used_percent=attrs.get("memory_used_percent"), swap_total_mb=attrs.get("swap_total_mb"),
                swap_used_mb=attrs.get("swap_used_mb"), swap_free_mb=attrs.get("swap_free_mb"), swap_used_percent=attrs.get("swap_used_percent"),
                rootfs_device=attrs.get("rootfs_device", ""), rootfs_mountpoint=attrs.get("rootfs_mountpoint", "/"), rootfs_total_gb=attrs.get("rootfs_total_gb"),
                rootfs_used_gb=attrs.get("rootfs_used_gb"), rootfs_free_gb=attrs.get("rootfs_free_gb"), rootfs_used_percent=attrs.get("rootfs_used_percent"),
                load_1m=attrs.get("load_1m"), load_5m=attrs.get("load_5m"), load_15m=attrs.get("load_15m"), uptime_seconds=attrs.get("uptime_seconds"),
                cpu_core_count=attrs.get("cpu_core_count"), cpu_model=attrs.get("cpu_model", ""), hostname=attrs.get("hostname", ""),
                network_interface=attrs.get("network_interface", ""), ipv4=attrs.get("ipv4", ""), network_rx_bytes=attrs.get("network_rx_bytes"),
                network_tx_bytes=attrs.get("network_tx_bytes"), throttled_raw=attrs.get("throttled_raw", ""), undervoltage=attrs.get("undervoltage"),
                frequency_capped=attrs.get("frequency_capped"), throttled=attrs.get("throttled"), soft_temp_limit=attrs.get("soft_temp_limit"),
                undervoltage_occurred=attrs.get("undervoltage_occurred"), frequency_capped_occurred=attrs.get("frequency_capped_occurred"),
                throttled_occurred=attrs.get("throttled_occurred"), soft_temp_limit_occurred=attrs.get("soft_temp_limit_occurred"),
                thermal_zones=attrs.get("thermal_zones", []),
            )
        except (KeyError, TypeError, ValueError):
            continue
    return None


def _realtime_from_host_relay(hass: HomeAssistant) -> RealtimeCoolingSnapshot | None:
    """Use the HA canonical/compat relay when realtime JSON is unavailable."""
    for entity_id in HOST_TELEMETRY_ENTITIES:
        state = hass.states.get(entity_id)
        if state is None:
            continue
        attrs = state.attributes
        try:
            sample_epoch = float(attrs.get("sample_epoch", 0))
            age = max(0.0, time.time() - sample_epoch)
            if sample_epoch <= 0 or age > HOST_TELEMETRY_MAX_AGE_SECONDS:
                continue
            temp = float(attrs["cpu_temperature"])
            if temp < -20 or temp > 150:
                continue
            rpm = int(float(attrs.get("fan_rpm", 0)))
            pwm_raw = attrs.get("fan_pwm", attrs.get("fan_pwm_raw"))
            if pwm_raw is None:
                continue
            pwm = max(0, min(255, int(float(pwm_raw))))
            percent_raw = attrs.get("fan_percent")
            percent = int(float(percent_raw)) if percent_raw is not None else round((pwm / 255) * 100)
            percent = max(0, min(100, percent))
            level = max(0, int(float(attrs.get("fan_level", 0))))
            max_level = max(0, int(float(attrs.get("fan_max_level", 0))))
            if max_level > 0:
                level = min(level, max_level)
            return RealtimeCoolingSnapshot(
                cpu_temperature=round(temp, 1), fan_rpm=max(0, rpm), fan_pwm=pwm,
                fan_percent=percent, fan_level=level, fan_max_level=max_level,
                sample_age_seconds=round(age, 2), available=True,
            )
        except (KeyError, TypeError, ValueError):
            continue
    return None


class SBC5Coordinator(DataUpdateCoordinator[SBC5CoordinatorData]):
    """Single coordinated poll for authoritative host telemetry and updates."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            update_interval=timedelta(seconds=15),
            always_update=False,
        )

    async def _async_update_data(self) -> SBC5CoordinatorData:
        # 2.8.22: prefer the shared JSON transport. It avoids coupling native
        # entities to the large REST relay, which is intentionally published slower.
        telemetry = await self.hass.async_add_executor_job(read_shared_telemetry)
        if telemetry is None:
            telemetry = _telemetry_from_host_relay(self.hass)
        if telemetry is None:
            telemetry = await self.hass.async_add_executor_job(read_telemetry)

        update_state = self.hass.states.get("sensor.sbc5_control_center_update")
        attrs: dict[str, Any] = dict(update_state.attributes) if update_state else {}
        state = update_state.state if update_state else "current"
        installed = str(attrs.get("installed_version") or APP_VERSION)
        latest = str(attrs.get("latest_version") or installed)

        ai_state = self.hass.states.get("sensor.sbc5_control_center_ai_runtime")
        ai_attrs: dict[str, Any] = dict(ai_state.attributes) if ai_state else {}
        ai_cooling = ai_attrs.get("ai_cooling")
        predictor = ai_cooling.get("thermal_predictor", {}) if isinstance(ai_cooling, dict) else {}
        thermal_predictor = dict(predictor) if isinstance(predictor, dict) else {}

        ethernet_health = await self.hass.async_add_executor_job(_read_ethernet_health, self.hass)

        app_update = AppUpdateInfo(
            state=state,
            installed_version=installed,
            latest_version=latest,
            source=str(attrs.get("source") or ""),
            repository=str(attrs.get("repository") or ""),
            release_url=str(attrs.get("release_url") or ""),
            download_url=str(attrs.get("download_url") or ""),
            changelog_url=str(attrs.get("changelog_url") or ""),
            restart_required=str(attrs.get("restart_required") or ""),
            release_date=str(attrs.get("release_date") or ""),
            summary=str(attrs.get("summary") or ""),
            local_package_file=str(attrs.get("local_package_file") or ""),
            local_install_supported=bool(attrs.get("local_install_supported", False)),
            runtime_app_slug=str(attrs.get("runtime_app_slug") or ""),
            update_scope=str(attrs.get("update_scope") or "full"),
            card_ui_installed_version=str(attrs.get("card_ui_installed_version") or ""),
            card_ui_latest_version=str(attrs.get("card_ui_latest_version") or ""),
        )
        return SBC5CoordinatorData(
            telemetry=telemetry, app_update=app_update, thermal_predictor=thermal_predictor, ethernet_health=ethernet_health
        )

class SBC5RealtimeCoordinator(DataUpdateCoordinator[RealtimeCoolingSnapshot]):
    """Balanced 5-second coordinator for CPU temperature and fan telemetry."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_realtime",
            config_entry=config_entry,
            update_interval=timedelta(seconds=5),
            always_update=False,
        )

    async def _async_update_data(self) -> RealtimeCoolingSnapshot:
        snapshot = await self.hass.async_add_executor_job(read_realtime_cooling)
        if snapshot.available:
            return snapshot
        relay = _realtime_from_host_relay(self.hass)
        return relay if relay is not None else snapshot

