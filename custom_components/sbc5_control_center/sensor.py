from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import time
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import APP_VERSION, DOMAIN
from .coordinator import SBC5Coordinator, SBC5CoordinatorData, SBC5RealtimeCoordinator
from .entity import SBC5CoordinatorEntity


@dataclass(frozen=True, kw_only=True)
class SensorSpec:
    unique_id: str
    name: str
    value_fn: Callable[[SBC5CoordinatorData], Any]
    icon: str | None = None
    unit: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None


def _predictor_number(data: SBC5CoordinatorData, key: str) -> float | None:
    value = data.thermal_predictor.get(key)
    try:
        return round(float(value), 2) if value is not None else None
    except (TypeError, ValueError):
        return None


def _predictor_nested_number(data: SBC5CoordinatorData, group: str, key: str) -> float | None:
    values = data.thermal_predictor.get(group)
    if not isinstance(values, dict):
        return None
    try:
        value = values.get(key)
        return round(float(value), 3) if value is not None else None
    except (TypeError, ValueError):
        return None


def _predictor_validated_total(data: SBC5CoordinatorData) -> int | None:
    direct = data.thermal_predictor.get("validated_samples_total")
    try:
        if direct is not None:
            return int(direct)
    except (TypeError, ValueError):
        pass
    values = data.thermal_predictor.get("validated_samples")
    if not isinstance(values, dict):
        return None
    total = 0
    found = False
    for horizon in ("30", "60", "120"):
        try:
            value = values.get(horizon)
            if value is not None:
                total += int(value)
                found = True
        except (TypeError, ValueError):
            continue
    return total if found else None


def _predictor_age_seconds(data: SBC5CoordinatorData) -> float | None:
    try:
        updated = float(data.thermal_predictor.get("updated_epoch"))
    except (TypeError, ValueError):
        return None
    if updated <= 0:
        return None
    return round(max(0.0, time.time() - updated), 1)


def _cpu_usage_percent(data: SBC5CoordinatorData) -> float | None:
    """Return normalized whole-host CPU usage from the four per-core samples."""
    values = [value for value in data.telemetry.cpu_core_usage_percent if value is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 1)


SENSOR_SPECS: tuple[SensorSpec, ...] = (
    SensorSpec(unique_id="sbc5_ai_thermal_forecast_30s", name="SBC5 AI Thermal Forecast 30s", value_fn=lambda d: _predictor_number(d, "forecast_30s_c"), icon="mdi:thermometer-chevron-up", unit=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_forecast_60s", name="SBC5 AI Thermal Forecast 60s", value_fn=lambda d: _predictor_number(d, "forecast_60s_c"), icon="mdi:thermometer-chevron-up", unit=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_forecast_120s", name="SBC5 AI Thermal Forecast 120s", value_fn=lambda d: _predictor_number(d, "forecast_120s_c"), icon="mdi:thermometer-chevron-up", unit=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_confidence", name="SBC5 AI Thermal Predictor Confidence", value_fn=lambda d: _predictor_number(d, "confidence_percent"), icon="mdi:brain", unit=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_quality", name="SBC5 AI Thermal Predictor Quality", value_fn=lambda d: d.thermal_predictor.get("quality_state") or None, icon="mdi:brain-check-outline"),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_mae", name="SBC5 AI Thermal Predictor Average MAE", value_fn=lambda d: _predictor_number(d, "average_mae_c"), icon="mdi:chart-bell-curve", unit=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_mae_30s", name="SBC5 AI Thermal Predictor MAE 30s", value_fn=lambda d: _predictor_nested_number(d, "mae_ema_c", "30"), icon="mdi:chart-timeline-variant", unit=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_mae_60s", name="SBC5 AI Thermal Predictor MAE 60s", value_fn=lambda d: _predictor_nested_number(d, "mae_ema_c", "60"), icon="mdi:chart-timeline-variant", unit=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_mae_120s", name="SBC5 AI Thermal Predictor MAE 120s", value_fn=lambda d: _predictor_nested_number(d, "mae_ema_c", "120"), icon="mdi:chart-timeline-variant", unit=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_last_error_30s", name="SBC5 AI Thermal Predictor Last Error 30s", value_fn=lambda d: _predictor_nested_number(d, "last_error_c", "30"), icon="mdi:delta", unit=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_last_error_60s", name="SBC5 AI Thermal Predictor Last Error 60s", value_fn=lambda d: _predictor_nested_number(d, "last_error_c", "60"), icon="mdi:delta", unit=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_last_error_120s", name="SBC5 AI Thermal Predictor Last Error 120s", value_fn=lambda d: _predictor_nested_number(d, "last_error_c", "120"), icon="mdi:delta", unit=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_slope", name="SBC5 AI Thermal Predictor Slope", value_fn=lambda d: _predictor_number(d, "slope_c_per_min"), icon="mdi:trending-up", unit="°C/min", state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_samples", name="SBC5 AI Thermal Predictor Validated Samples", value_fn=_predictor_validated_total, icon="mdi:counter", state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_age", name="SBC5 AI Thermal Predictor Data Age", value_fn=_predictor_age_seconds, icon="mdi:timer-sand", unit="s", state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_shadow_delta", name="SBC5 AI Thermal Shadow Delta", value_fn=lambda d: _predictor_nested_number(d, "shadow_assist", "suggested_delta_pp"), icon="mdi:plus-minus-variant", unit="pp", state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_shadow_pwm", name="SBC5 AI Thermal Shadow PWM", value_fn=lambda d: _predictor_nested_number(d, "shadow_assist", "suggested_pwm_percent"), icon="mdi:fan-auto", unit=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_shadow_state", name="SBC5 AI Thermal Shadow State", value_fn=lambda d: (d.thermal_predictor.get("shadow_assist") or {}).get("gate_reason") if isinstance(d.thermal_predictor.get("shadow_assist"), dict) else None, icon="mdi:shield-search"),
    SensorSpec(unique_id="sbc5_ai_thermal_shadow_decision", name="SBC5 AI Thermal Shadow Decision", value_fn=lambda d: (d.thermal_predictor.get("shadow_assist") or {}).get("decision_reason") if isinstance(d.thermal_predictor.get("shadow_assist"), dict) else None, icon="mdi:brain"),
    SensorSpec(unique_id="sbc5_ai_thermal_shadow_weighted_forecast", name="SBC5 AI Thermal Shadow Weighted Forecast", value_fn=lambda d: _predictor_nested_number(d, "shadow_assist", "weighted_forecast_c"), icon="mdi:thermometer-lines", unit=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ethernet_health", name="SBC5 Ethernet Health", value_fn=lambda d: d.ethernet_health.get("health") or None, icon="mdi:ethernet"),
    SensorSpec(unique_id="sbc5_ethernet_link_flaps", name="SBC5 Ethernet Link Flaps", value_fn=lambda d: d.ethernet_health.get("flap_count_window"), icon="mdi:swap-horizontal-bold", state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ethernet_eee_status", name="SBC5 Ethernet EEE Status", value_fn=lambda d: d.ethernet_health.get("eee_status") or None, icon="mdi:leaf-off"),
    SensorSpec(unique_id="sbc5_network_mac", name="SBC5 Network MAC", value_fn=lambda d: d.telemetry.network_mac or None, icon="mdi:lan-connect"),
    SensorSpec(unique_id="sbc5_network_interface", name="SBC5 Network Interface", value_fn=lambda d: d.telemetry.network_interface or None, icon="mdi:ethernet"),
    SensorSpec(unique_id="sbc5_cpu_temperature", name="SBC5 CPU Temperature",
               value_fn=lambda d: d.telemetry.cpu_temperature, icon="mdi:thermometer",
               unit=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE,
               state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_cpu_frequency", name="SBC5 CPU Frequency",
               value_fn=lambda d: d.telemetry.cpu_frequency_mhz, icon="mdi:speedometer",
               unit="MHz", state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_cpu_usage", name="SBC5 CPU Usage",
               value_fn=_cpu_usage_percent, icon="mdi:cpu-64-bit",
               unit=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_cpu_core_0_frequency", name="SBC5 CPU Core 0 Frequency",
               value_fn=lambda d: d.telemetry.cpu_core_frequencies_mhz[0], icon="mdi:chip",
               unit="MHz", state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_cpu_core_1_frequency", name="SBC5 CPU Core 1 Frequency",
               value_fn=lambda d: d.telemetry.cpu_core_frequencies_mhz[1], icon="mdi:chip",
               unit="MHz", state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_cpu_core_2_frequency", name="SBC5 CPU Core 2 Frequency",
               value_fn=lambda d: d.telemetry.cpu_core_frequencies_mhz[2], icon="mdi:chip",
               unit="MHz", state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_cpu_core_3_frequency", name="SBC5 CPU Core 3 Frequency",
               value_fn=lambda d: d.telemetry.cpu_core_frequencies_mhz[3], icon="mdi:chip",
               unit="MHz", state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_cpu_core_0_usage", name="SBC5 CPU Core 0 Usage",
               value_fn=lambda d: d.telemetry.cpu_core_usage_percent[0], icon="mdi:cpu-64-bit",
               unit=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_cpu_core_1_usage", name="SBC5 CPU Core 1 Usage",
               value_fn=lambda d: d.telemetry.cpu_core_usage_percent[1], icon="mdi:cpu-64-bit",
               unit=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_cpu_core_2_usage", name="SBC5 CPU Core 2 Usage",
               value_fn=lambda d: d.telemetry.cpu_core_usage_percent[2], icon="mdi:cpu-64-bit",
               unit=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_cpu_core_3_usage", name="SBC5 CPU Core 3 Usage",
               value_fn=lambda d: d.telemetry.cpu_core_usage_percent[3], icon="mdi:cpu-64-bit",
               unit=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_fan_rpm", name="SBC5 Fan RPM",
               value_fn=lambda d: d.telemetry.fan_rpm, icon="mdi:fan", unit="RPM",
               state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_fan_pwm", name="SBC5 Fan PWM",
               value_fn=lambda d: d.telemetry.fan_pwm, icon="mdi:fan-speed-3",
               state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_fan_level", name="SBC5 Fan Level",
               value_fn=lambda d: d.telemetry.fan_level, icon="mdi:fan-speed-2",
               state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_fan_max_level", name="SBC5 Fan Max Level",
               value_fn=lambda d: d.telemetry.fan_max_level, icon="mdi:stairs",
               state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_fan_percent", name="SBC5 Fan Percent",
               value_fn=lambda d: d.telemetry.fan_percent, icon="mdi:fan-speed-2",
               unit=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_usb_current_limit", name="SBC5 USB Current Limit",
               value_fn=lambda d: d.telemetry.usb_current_limit_ma, icon="mdi:usb-port",
               unit=UnitOfElectricCurrent.MILLIAMPERE, device_class=SensorDeviceClass.CURRENT),
    SensorSpec(unique_id="sbc5_input_voltage", name="SBC5 Input Voltage",
               value_fn=lambda d: d.telemetry.input_voltage_v, icon="mdi:flash",
               unit=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE,
               state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_pmic_power", name="SBC5 PMIC Measured Power",
               value_fn=lambda d: d.telemetry.pmic_power_w, icon="mdi:lightning-bolt",
               unit=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER,
               state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_pmic_equivalent_current", name="SBC5 PMIC Equivalent Input Current",
               value_fn=lambda d: d.telemetry.pmic_equivalent_current_a, icon="mdi:current-dc",
               unit=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT,
               state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_pmic_temperature", name="SBC5 PMIC Temperature",
               value_fn=lambda d: d.telemetry.pmic_temperature_c, icon="mdi:thermometer-lines",
               unit=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE,
               state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_core_current", name="SBC5 VDD Core Current",
               value_fn=lambda d: d.telemetry.core_current_a, icon="mdi:current-dc",
               unit=UnitOfElectricCurrent.AMPERE, device_class=SensorDeviceClass.CURRENT,
               state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_core_voltage", name="SBC5 VDD Core Voltage",
               value_fn=lambda d: d.telemetry.core_voltage_v, icon="mdi:sine-wave",
               unit=UnitOfElectricPotential.VOLT, device_class=SensorDeviceClass.VOLTAGE,
               state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_core_power", name="SBC5 VDD Core Power",
               value_fn=lambda d: d.telemetry.core_power_w, icon="mdi:chip",
               unit=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER,
               state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_usb_declared_current", name="SBC5 USB Declared Current",
               value_fn=lambda d: d.telemetry.usb_declared_current_ma, icon="mdi:usb",
               unit=UnitOfElectricCurrent.MILLIAMPERE, device_class=SensorDeviceClass.CURRENT,
               state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_usb_device_count", name="SBC5 USB Device Count",
               value_fn=lambda d: d.telemetry.usb_device_count, icon="mdi:usb-port",
               state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_memory_used_percent", name="SBC5 Memory Used",
               value_fn=lambda d: d.telemetry.memory_used_percent, icon="mdi:memory",
               unit=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_memory_used", name="SBC5 Memory Used MB",
               value_fn=lambda d: d.telemetry.memory_used_mb, icon="mdi:memory",
               unit="MB", state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_memory_available", name="SBC5 Memory Available MB",
               value_fn=lambda d: d.telemetry.memory_available_mb, icon="mdi:memory-arrow-down",
               unit="MB", state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_swap_used_percent", name="SBC5 Swap Used",
               value_fn=lambda d: d.telemetry.swap_used_percent, icon="mdi:swap-horizontal",
               unit=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_rootfs_used_percent", name="SBC5 Rootfs Used",
               value_fn=lambda d: d.telemetry.rootfs_used_percent, icon="mdi:harddisk",
               unit=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_rootfs_used", name="SBC5 Rootfs Used GB",
               value_fn=lambda d: d.telemetry.rootfs_used_gb, icon="mdi:harddisk",
               unit="GB", state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_load_1m", name="SBC5 Load 1m",
               value_fn=lambda d: d.telemetry.load_1m, icon="mdi:chart-line",
               state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_load_5m", name="SBC5 Load 5m",
               value_fn=lambda d: d.telemetry.load_5m, icon="mdi:chart-line",
               state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_load_15m", name="SBC5 Load 15m",
               value_fn=lambda d: d.telemetry.load_15m, icon="mdi:chart-line-variant",
               state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_uptime_hours", name="SBC5 Uptime Hours",
               value_fn=lambda d: round((d.telemetry.uptime_seconds or 0) / 3600, 1) if d.telemetry.uptime_seconds is not None else None,
               icon="mdi:timer-outline", unit="h", state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_cpu_core_count", name="SBC5 CPU Core Count",
               value_fn=lambda d: d.telemetry.cpu_core_count, icon="mdi:cpu-64-bit",
               state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_os", name="SBC5 Operating System",
               value_fn=lambda d: d.telemetry.os_pretty_name or d.telemetry.os_name or None, icon="mdi:home-assistant"),
    SensorSpec(unique_id="sbc5_kernel", name="SBC5 Kernel",
               value_fn=lambda d: d.telemetry.kernel_version or None, icon="mdi:linux"),
    SensorSpec(unique_id="sbc5_architecture", name="SBC5 Architecture",
               value_fn=lambda d: d.telemetry.architecture or None, icon="mdi:chip"),
    SensorSpec(unique_id="sbc5_firmware", name="SBC5 Raspberry Pi Firmware",
               value_fn=lambda d: d.telemetry.firmware_version or None, icon="mdi:memory"),
    SensorSpec(unique_id="sbc5_bootloader_firmware", name="SBC5 Bootloader Firmware",
               value_fn=lambda d: d.telemetry.bootloader_version or None, icon="mdi:memory-arrow-up"),
    SensorSpec(unique_id="sbc5_network_rx_bytes", name="SBC5 Network RX Bytes",
               value_fn=lambda d: d.telemetry.network_rx_bytes, icon="mdi:download-network-outline",
               unit="B", state_class=SensorStateClass.TOTAL_INCREASING),
    SensorSpec(unique_id="sbc5_network_tx_bytes", name="SBC5 Network TX Bytes",
               value_fn=lambda d: d.telemetry.network_tx_bytes, icon="mdi:upload-network-outline",
               unit="B", state_class=SensorStateClass.TOTAL_INCREASING),
    SensorSpec(unique_id="sbc5_thermal_zone_max", name="SBC5 Max Thermal Zone",
               value_fn=lambda d: max((float(z.get("temp_c", 0)) for z in d.telemetry.thermal_zones), default=None),
               icon="mdi:thermometer-high", unit=UnitOfTemperature.CELSIUS,
               device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: SBC5Coordinator = entry.runtime_data
    overrides: dict[str, str] = hass.data.get(DOMAIN, {}).get("entity_id_overrides", {})

    def eid(unique_id: str) -> str:
        return overrides.get(unique_id) or f"sensor.{unique_id}"

    realtime = SBC5RealtimeCoordinator(hass, entry)
    await realtime.async_config_entry_first_refresh()
    realtime_ids = {
        "sbc5_cpu_temperature", "sbc5_fan_rpm", "sbc5_fan_pwm",
        "sbc5_fan_percent", "sbc5_fan_level", "sbc5_fan_max_level",
    }
    entities: list[SensorEntity] = [
        (SBC5RealtimeNumericSensor(realtime, coordinator, spec, eid(spec.unique_id))
         if spec.unique_id in realtime_ids
         else SBC5NumericSensor(coordinator, spec, eid(spec.unique_id)))
        for spec in SENSOR_SPECS
    ]
    entities.extend([
        SBC5CoolingStatusSensor(coordinator, eid("sbc5_cooling_status")),
        SBC5PowerSupplySensor(coordinator, eid("sbc5_power_supply")),
        SBC5BootConfigurationSensor(coordinator, eid("sbc5_boot_configuration")),
        SBC5OverclockStatusSensor(coordinator, eid("sbc5_overclock_status")),
        SBC5SystemInfoSensor(coordinator, eid("sbc5_system_info")),
        SBC5ThrottlingStatusSensor(coordinator, eid("sbc5_throttling_status")),
        SBC5PackageVersionSensor(coordinator, eid("sbc5_package_version")),
    ])
    async_add_entities(entities)


class SBC5RealtimeNumericSensor(SBC5CoordinatorEntity, SensorEntity):
    """Fast 1-second sensors without waking the full telemetry coordinator."""

    def __init__(self, realtime: SBC5RealtimeCoordinator, base: SBC5Coordinator, spec: SensorSpec, entity_id_override: str | None) -> None:
        super().__init__(realtime, spec.unique_id, spec.name, entity_id_override)
        self._realtime = realtime
        self._base = base
        self._spec = spec
        self._attr_icon = spec.icon
        self._attr_native_unit_of_measurement = spec.unit
        self._attr_device_class = spec.device_class
        self._attr_state_class = spec.state_class

    @property
    def native_value(self) -> Any:
        rt = self._realtime.data
        if rt.available:
            values = {
                "sbc5_cpu_temperature": rt.cpu_temperature,
                "sbc5_fan_rpm": rt.fan_rpm,
                "sbc5_fan_pwm": rt.fan_pwm,
                "sbc5_fan_percent": rt.fan_percent,
                "sbc5_fan_level": rt.fan_level,
                "sbc5_fan_max_level": rt.fan_max_level,
            }
            if self._spec.unique_id in values:
                return values[self._spec.unique_id]
        return self._spec.value_fn(self._base.data)

    @property
    def available(self) -> bool:
        return self.native_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        rt = self._realtime.data
        attrs: dict[str, Any] = {
            "telemetry_source": "app_realtime_json" if rt.available else self._base.data.telemetry.telemetry_source,
            "refresh_interval_s": 5,
        }
        if self._spec.unique_id in {"sbc5_fan_pwm", "sbc5_fan_percent"}:
            attrs["raw_pwm"] = rt.fan_pwm if rt.available else self._base.data.telemetry.fan_pwm
        return attrs


class SBC5NumericSensor(SBC5CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: SBC5Coordinator, spec: SensorSpec, entity_id_override: str | None) -> None:
        super().__init__(coordinator, spec.unique_id, spec.name, entity_id_override)
        self._spec = spec
        self._attr_icon = spec.icon
        self._attr_native_unit_of_measurement = spec.unit
        self._attr_device_class = spec.device_class
        self._attr_state_class = spec.state_class

    @property
    def native_value(self) -> Any:
        return self._spec.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        t = self.coordinator.data.telemetry
        if self._spec.unique_id.startswith("sbc5_pmic_") or self._spec.unique_id.startswith("sbc5_core_") or self._spec.unique_id == "sbc5_input_voltage":
            return t.pmic_available and self.native_value is not None
        return self.native_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        t = self.coordinator.data.telemetry
        if self._spec.unique_id in {"sbc5_fan_pwm", "sbc5_fan_percent"}:
            return {"raw_pwm": t.fan_pwm, "telemetry_source": t.telemetry_source}
        if self._spec.unique_id == "sbc5_cpu_frequency":
            return {"min_mhz": t.cpu_frequency_min_mhz, "max_mhz": t.cpu_frequency_max_mhz, "governor": t.cpu_governor or None, "telemetry_source": t.telemetry_source}
        if self._spec.unique_id == "sbc5_usb_current_limit":
            return {"high_current_enabled": t.usb_high_current, "over_current_detected": t.usb_over_current_detected, "usb_limit_source": t.usb_limit_source, "usb_max_current_enable": t.usb_config_override, "shared_across_usb_a_ports": True, "telemetry_source": t.telemetry_source}
        if self._spec.unique_id == "sbc5_pmic_power":
            return {
                "rails": list(t.pmic_rails),
                "input_voltage_v": t.input_voltage_v,
                "equivalent_input_current_a": t.pmic_equivalent_current_a,
                "measurement_source": t.pmic_source,
                "important": "Suma mocy szyn PMIC nie obejmuje USB ani obciążeń podłączonych bezpośrednio do 5 V.",
            }
        if self._spec.unique_id == "sbc5_pmic_equivalent_current":
            return {
                "calculation": "pmic_power_w / EXT5V_V",
                "actual_psu_input_current": False,
                "important": "To prąd równoważny dla mocy mierzonej przez PMIC, nie całkowity prąd z zasilacza.",
            }
        if self._spec.unique_id == "sbc5_usb_declared_current":
            return {
                "devices": list(t.usb_devices),
                "device_count": t.usb_device_count,
                "usb_limit_ma": t.usb_current_limit_ma,
                "is_instantaneous_measurement": False,
                "important": "bMaxPower to deklarowany maksymalny pobór konfiguracji USB, nie chwilowy pobór prądu.",
            }
        if self._spec.unique_id == "sbc5_usb_device_count":
            return {"devices": list(t.usb_devices)}
        if self._spec.unique_id in {"sbc5_memory_used_percent", "sbc5_memory_used", "sbc5_memory_available"}:
            return {
                "memory_total_mb": t.memory_total_mb,
                "memory_used_mb": t.memory_used_mb,
                "memory_available_mb": t.memory_available_mb,
                "memory_used_percent": t.memory_used_percent,
            }
        if self._spec.unique_id == "sbc5_swap_used_percent":
            return {
                "swap_total_mb": t.swap_total_mb,
                "swap_used_mb": t.swap_used_mb,
                "swap_free_mb": t.swap_free_mb,
                "swap_used_percent": t.swap_used_percent,
            }
        if self._spec.unique_id in {"sbc5_rootfs_used_percent", "sbc5_rootfs_used"}:
            return {
                "rootfs_device": t.rootfs_device or None,
                "rootfs_mountpoint": t.rootfs_mountpoint,
                "rootfs_total_gb": t.rootfs_total_gb,
                "rootfs_used_gb": t.rootfs_used_gb,
                "rootfs_free_gb": t.rootfs_free_gb,
                "rootfs_used_percent": t.rootfs_used_percent,
            }
        if self._spec.unique_id in {"sbc5_load_1m", "sbc5_load_5m", "sbc5_load_15m", "sbc5_uptime_hours"}:
            return {
                "load_1m": t.load_1m,
                "load_5m": t.load_5m,
                "load_15m": t.load_15m,
                "uptime_seconds": t.uptime_seconds,
            }
        if self._spec.unique_id == "sbc5_cpu_core_count":
            return {"cpu_model": t.cpu_model or None, "architecture": t.architecture or None}
        if self._spec.unique_id == "sbc5_os":
            return {"name": t.os_name or None, "version": t.os_version or None, "pretty_name": t.os_pretty_name or None}
        if self._spec.unique_id == "sbc5_kernel":
            return {"architecture": t.architecture or None, "hostname": t.hostname or None}
        if self._spec.unique_id == "sbc5_architecture":
            return {"cpu_model": t.cpu_model or None, "cpu_cores": t.cpu_core_count}
        if self._spec.unique_id == "sbc5_firmware":
            return {"firmware_build": t.firmware_build or None}
        if self._spec.unique_id == "sbc5_bootloader_firmware":
            return {"board_revision": t.board_revision or None, "hardware_revision": t.hardware_revision or None}
        if self._spec.unique_id in {"sbc5_network_rx_bytes", "sbc5_network_tx_bytes"}:
            return {"interface": t.network_interface or None, "ipv4": t.ipv4 or None, "hostname": t.hostname or None}
        if self._spec.unique_id == "sbc5_thermal_zone_max":
            return {"thermal_zones": list(t.thermal_zones)}
        return None


class SBC5CoolingStatusSensor(SBC5CoordinatorEntity, SensorEntity):
    _attr_icon = "mdi:snowflake-thermometer"

    def __init__(self, coordinator: SBC5Coordinator, entity_id_override: str | None) -> None:
        super().__init__(coordinator, "sbc5_cooling_status", "SBC5 Cooling Status", entity_id_override)

    @property
    def native_value(self) -> str:
        return self.coordinator.data.telemetry.cooling_status

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        t = self.coordinator.data.telemetry
        return {"punkt": t.fan_level, "punktow_max": t.fan_max_level, "pwm_proc": t.fan_percent, "rpm": t.fan_rpm, "raw_pwm": t.fan_pwm, "telemetry_source": t.telemetry_source}


class SBC5PowerSupplySensor(SBC5CoordinatorEntity, SensorEntity):
    _attr_icon = "mdi:power-plug-battery"

    def __init__(self, coordinator: SBC5Coordinator, entity_id_override: str | None) -> None:
        super().__init__(coordinator, "sbc5_power_supply", "SBC5 Power Supply", entity_id_override)

    @property
    def native_value(self) -> str:
        return self.coordinator.data.telemetry.power_supply

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        t = self.coordinator.data.telemetry
        return {
            "type": t.power_supply_type,
            "official_raspberry_pi_supply": t.power_supply_official,
            "usb_pd_detected": t.power_supply_pd_detected,
            "usb_pd_5a_capable": t.power_supply_pd_5a_capable,
            "usb_vid": t.power_supply_vid or None,
            "product_vdo": t.power_supply_product_vdo or None,
            "max_current_ma": t.power_max_current_ma,
            "detection_source": t.power_detection_source,
            "input_voltage_v": t.input_voltage_v,
            "pmic_measured_power_w": t.pmic_power_w,
            "pmic_equivalent_current_a": t.pmic_equivalent_current_a,
            "usb_current_limit_ma": t.usb_current_limit_ma,
            "usb_declared_current_ma": t.usb_declared_current_ma,
            "usb_device_count": t.usb_device_count,
            "high_current_enabled": t.usb_high_current,
            "usb_limit_source": t.usb_limit_source,
            "usb_max_current_enable": t.usb_config_override,
            "over_current_detected": t.usb_over_current_detected,
            "over_current_source": t.over_current_source,
            "telemetry_source": t.telemetry_source,
        }


class SBC5BootConfigurationSensor(SBC5CoordinatorEntity, SensorEntity):
    _attr_icon = "mdi:file-cog-outline"

    def __init__(self, coordinator: SBC5Coordinator, entity_id_override: str | None) -> None:
        super().__init__(coordinator, "sbc5_boot_configuration", "SBC5 Boot Configuration", entity_id_override)

    @property
    def native_value(self) -> str:
        t = self.coordinator.data.telemetry
        return "Odczytano" if t.boot_config_available else "Niedostępna"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        t = self.coordinator.data.telemetry
        return {
            "device": t.boot_config_device or None,
            "path": t.boot_config_path or None,
            "discovery_source": t.boot_config_source or None,
            "exact_location": f"{t.boot_config_device}/{t.boot_config_path}" if t.boot_config_device and t.boot_config_path else None,
            "sha256": t.boot_config_sha256 or None,
            "entry_count": t.boot_config_entry_count,
            "entries_truncated": t.boot_config_truncated,
            "entries": list(t.boot_config_entries),
            "includes": list(t.boot_config_includes),
            "dtoverlays": list(t.boot_config_overlays),
            "dtparams": list(t.boot_config_dtparams),
            "active_vcgencmd_int": dict(t.active_config_int),
            "active_vcgencmd_str": dict(t.active_config_str),
            "bootloader_config": dict(t.bootloader_config),
            "rpi_model": t.rpi_model or None,
            "architecture": t.architecture or None,
            "kernel_version": t.kernel_version or None,
            "kernel_cmdline": t.kernel_cmdline or None,
            "refresh_interval_s": 60,
            "note": "Sekcje warunkowe config.txt są zachowane w atrybucie section; wartości aktywne są porównywane z vcgencmd i stanem kernela.",
        }


class SBC5OverclockStatusSensor(SBC5CoordinatorEntity, SensorEntity):
    _attr_icon = "mdi:speedometer-slow"

    def __init__(self, coordinator: SBC5Coordinator, entity_id_override: str | None) -> None:
        super().__init__(coordinator, "sbc5_overclock_status", "SBC5 CPU / Overclock Status", entity_id_override)

    @property
    def native_value(self) -> str:
        return self.coordinator.data.telemetry.config_status

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        t = self.coordinator.data.telemetry
        return {
            "saved_arm_freq_mhz": t.saved_arm_freq_mhz,
            "active_arm_freq_mhz": t.active_arm_freq_mhz,
            "runtime_cpu_frequency_mhz": t.cpu_frequency_mhz,
            "runtime_min_mhz": t.cpu_frequency_min_mhz,
            "runtime_max_mhz": t.cpu_frequency_max_mhz,
            "governor": t.cpu_governor or None,
            "saved_core_freq_mhz": t.saved_core_freq_mhz,
            "active_core_freq_mhz": t.active_core_freq_mhz,
            "saved_gpu_freq_mhz": t.saved_gpu_freq_mhz,
            "active_gpu_freq_mhz": t.active_gpu_freq_mhz,
            "saved_over_voltage": t.saved_over_voltage or None,
            "active_over_voltage": t.active_over_voltage or None,
            "saved_over_voltage_delta": t.saved_over_voltage_delta or None,
            "active_over_voltage_delta": t.active_over_voltage_delta or None,
            "saved_usb_max_current_enable": t.saved_usb_max_current_enable,
            "active_usb_max_current_enable": t.active_usb_max_current_enable,
            "saved_arm_64bit": t.saved_arm_64bit,
            "active_arm_64bit": t.active_arm_64bit,
            "saved_differs_from_active": t.config_pending_restart,
            "comparison_note": "v1.9.10 zachowuje zbalansowane odświeżanie 5 s i telemetrię czterech rdzeni; rozbieżność zapis/aktywne zwykle oznacza oczekujący reboot.",
        }


class SBC5SystemInfoSensor(SBC5CoordinatorEntity, SensorEntity):
    _attr_icon = "mdi:raspberry-pi"

    def __init__(self, coordinator: SBC5Coordinator, entity_id_override: str | None) -> None:
        super().__init__(coordinator, "sbc5_system_info", "SBC5 System Info", entity_id_override)

    @property
    def native_value(self) -> str:
        t = self.coordinator.data.telemetry
        return t.rpi_model or t.cpu_model or "Raspberry Pi 5"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        t = self.coordinator.data.telemetry
        return {
            "cpu_model": t.cpu_model or None,
            "cpu_cores": t.cpu_core_count,
            "rpi_model": t.rpi_model or None,
            "model_id": t.board_revision.upper() if t.board_revision else None,
            "hardware_revision": t.hardware_revision or None,
            "serial_number": t.serial_number or None,
            "architecture": t.architecture or None,
            "kernel_version": t.kernel_version or None,
            "os_name": t.os_name or None,
            "os_version": t.os_version or None,
            "os_pretty_name": t.os_pretty_name or None,
            "firmware_version": t.firmware_version or None,
            "firmware_build": t.firmware_build or None,
            "bootloader_version": t.bootloader_version or None,
            "hostname": t.hostname or None,
            "network_mac": t.network_mac or None,
            "network_interface": t.network_interface or None,
            "ipv4": t.ipv4 or None,
            "network_rx_bytes": t.network_rx_bytes,
            "network_tx_bytes": t.network_tx_bytes,
            "memory_total_mb": t.memory_total_mb,
            "rootfs_total_gb": t.rootfs_total_gb,
            "thermal_zones": list(t.thermal_zones),
            "telemetry_source": t.telemetry_source,
        }


class SBC5ThrottlingStatusSensor(SBC5CoordinatorEntity, SensorEntity):
    _attr_icon = "mdi:gauge"

    def __init__(self, coordinator: SBC5Coordinator, entity_id_override: str | None) -> None:
        super().__init__(coordinator, "sbc5_throttling_status", "SBC5 Throttling Status", entity_id_override)

    @property
    def native_value(self) -> str:
        t = self.coordinator.data.telemetry
        if t.undervoltage is None and t.throttled is None and not t.throttled_raw:
            return "Niedostępne"
        active = []
        if t.undervoltage:
            active.append("Undervoltage")
        if t.frequency_capped:
            active.append("Frequency capped")
        if t.throttled:
            active.append("Throttling")
        if t.soft_temp_limit:
            active.append("Soft temp limit")
        return ", ".join(active) if active else "OK"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        t = self.coordinator.data.telemetry
        return {
            "raw": t.throttled_raw or None,
            "undervoltage": t.undervoltage,
            "frequency_capped": t.frequency_capped,
            "throttled": t.throttled,
            "soft_temp_limit": t.soft_temp_limit,
            "undervoltage_occurred": t.undervoltage_occurred,
            "frequency_capped_occurred": t.frequency_capped_occurred,
            "throttled_occurred": t.throttled_occurred,
            "soft_temp_limit_occurred": t.soft_temp_limit_occurred,
            "note": "Dane pochodzą z vcgencmd get_throttled, jeżeli polecenie jest dostępne w środowisku SBC5 Control Center.",
        }


class SBC5PackageVersionSensor(SBC5CoordinatorEntity, SensorEntity):
    _attr_icon = "mdi:package-variant-closed"

    def __init__(self, coordinator: SBC5Coordinator, entity_id_override: str | None) -> None:
        super().__init__(coordinator, "sbc5_package_version", "SBC5 Control Center Version", entity_id_override)

    @property
    def native_value(self) -> str:
        return APP_VERSION
