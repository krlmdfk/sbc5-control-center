from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SBC5Coordinator
from .entity import SBC5CoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SBC5Coordinator = entry.runtime_data
    overrides: dict[str, str] = hass.data.get(DOMAIN, {}).get("entity_id_overrides", {})

    def eid(unique_id: str) -> str:
        return overrides.get(unique_id) or f"binary_sensor.{unique_id}"

    async_add_entities(
        [
            SBC5CoolingProblemBinarySensor(coordinator, eid("sbc5_cooling_problem")),
            SBC5HighTemperatureBinarySensor(coordinator, eid("sbc5_high_temperature")),
            SBC5LocalUpdateBinarySensor(coordinator, eid("sbc5_local_package_update_available")),
            SBC5ConfigPendingRestartBinarySensor(coordinator, eid("sbc5_config_pending_restart")),
            SBC5HighMemoryUsageBinarySensor(coordinator, eid("sbc5_high_memory_usage")),
            SBC5LowDiskSpaceBinarySensor(coordinator, eid("sbc5_low_disk_space")),
            SBC5ThrottlingProblemBinarySensor(coordinator, eid("sbc5_throttling_problem")),
            SBC5PowerIssueHistoryBinarySensor(coordinator, eid("sbc5_power_issue_history")),
        ]
    )


class SBC5CoolingProblemBinarySensor(SBC5CoordinatorEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:fan-alert"

    def __init__(self, coordinator: SBC5Coordinator, entity_id_override: str | None) -> None:
        super().__init__(coordinator, "sbc5_cooling_problem", "SBC5 Cooling Problem", entity_id_override)

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.telemetry.cooling_problem


class SBC5HighTemperatureBinarySensor(SBC5CoordinatorEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:thermometer-alert"

    def __init__(self, coordinator: SBC5Coordinator, entity_id_override: str | None) -> None:
        super().__init__(coordinator, "sbc5_high_temperature", "SBC5 High Temperature", entity_id_override)

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.telemetry.high_temperature


class SBC5LocalUpdateBinarySensor(SBC5CoordinatorEntity, BinarySensorEntity):
    _attr_icon = "mdi:archive-arrow-up"

    def __init__(self, coordinator: SBC5Coordinator, entity_id_override: str | None) -> None:
        super().__init__(
            coordinator,
            "sbc5_local_package_update_available",
            "SBC5 Local Package Update Available",
            entity_id_override,
        )

    @property
    def is_on(self) -> bool:
        update = self.coordinator.data.app_update
        return update.state == "available" and update.source == "local_zip"


class SBC5ConfigPendingRestartBinarySensor(SBC5CoordinatorEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:restart-alert"

    def __init__(self, coordinator: SBC5Coordinator, entity_id_override: str | None) -> None:
        super().__init__(coordinator, "sbc5_config_pending_restart", "SBC5 Config Differs From Active", entity_id_override)

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.telemetry.config_pending_restart

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        t = self.coordinator.data.telemetry
        return {
            "status": t.config_status,
            "saved_arm_freq_mhz": t.saved_arm_freq_mhz,
            "active_arm_freq_mhz": t.active_arm_freq_mhz,
            "note": "ON oznacza wykrytą rozbieżność między zapisem config.txt a odczytem aktywnym; po zmianie ustawień zwykle wymaga rebootu hosta.",
        }


class SBC5HighMemoryUsageBinarySensor(SBC5CoordinatorEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:memory"

    def __init__(self, coordinator: SBC5Coordinator, entity_id_override: str | None) -> None:
        super().__init__(coordinator, "sbc5_high_memory_usage", "SBC5 High Memory Usage", entity_id_override)

    @property
    def is_on(self) -> bool:
        used = self.coordinator.data.telemetry.memory_used_percent
        return used is not None and used >= 90

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        t = self.coordinator.data.telemetry
        return {
            "memory_total_mb": t.memory_total_mb,
            "memory_used_mb": t.memory_used_mb,
            "memory_available_mb": t.memory_available_mb,
            "memory_used_percent": t.memory_used_percent,
            "threshold_percent": 90,
        }


class SBC5LowDiskSpaceBinarySensor(SBC5CoordinatorEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:harddisk-alert"

    def __init__(self, coordinator: SBC5Coordinator, entity_id_override: str | None) -> None:
        super().__init__(coordinator, "sbc5_low_disk_space", "SBC5 Low Disk Space", entity_id_override)

    @property
    def is_on(self) -> bool:
        used = self.coordinator.data.telemetry.rootfs_used_percent
        return used is not None and used >= 90

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        t = self.coordinator.data.telemetry
        return {
            "rootfs_device": t.rootfs_device or None,
            "rootfs_mountpoint": t.rootfs_mountpoint,
            "rootfs_total_gb": t.rootfs_total_gb,
            "rootfs_used_gb": t.rootfs_used_gb,
            "rootfs_free_gb": t.rootfs_free_gb,
            "rootfs_used_percent": t.rootfs_used_percent,
            "threshold_percent": 90,
        }


class SBC5ThrottlingProblemBinarySensor(SBC5CoordinatorEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:gauge-full"

    def __init__(self, coordinator: SBC5Coordinator, entity_id_override: str | None) -> None:
        super().__init__(coordinator, "sbc5_throttling_problem", "SBC5 Throttling Problem", entity_id_override)

    @property
    def is_on(self) -> bool:
        t = self.coordinator.data.telemetry
        return bool(t.undervoltage or t.frequency_capped or t.throttled or t.soft_temp_limit)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        t = self.coordinator.data.telemetry
        return {
            "raw": t.throttled_raw or None,
            "undervoltage": t.undervoltage,
            "frequency_capped": t.frequency_capped,
            "throttled": t.throttled,
            "soft_temp_limit": t.soft_temp_limit,
        }


class SBC5PowerIssueHistoryBinarySensor(SBC5CoordinatorEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:history"

    def __init__(self, coordinator: SBC5Coordinator, entity_id_override: str | None) -> None:
        super().__init__(coordinator, "sbc5_power_issue_history", "SBC5 Power Issue History", entity_id_override)

    @property
    def is_on(self) -> bool:
        t = self.coordinator.data.telemetry
        return bool(t.undervoltage_occurred or t.frequency_capped_occurred or t.throttled_occurred or t.soft_temp_limit_occurred)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        t = self.coordinator.data.telemetry
        return {
            "raw": t.throttled_raw or None,
            "undervoltage_occurred": t.undervoltage_occurred,
            "frequency_capped_occurred": t.frequency_capped_occurred,
            "throttled_occurred": t.throttled_occurred,
            "soft_temp_limit_occurred": t.soft_temp_limit_occurred,
        }
