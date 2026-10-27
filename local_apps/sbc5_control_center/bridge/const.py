from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "sbc5_control_center"
LEGACY_DOMAIN = "rpi5_control_center_bridge"
OLDER_LEGACY_DOMAIN = "rpi5_fan_manager_bridge"
APP_VERSION = "3.1.6"
CONFIG_ENTRY_UNIQUE_ID = "sbc5_control_center"
DEVICE_IDENTIFIER = "sbc5_control_center"
DEVICE_NAME = "SBC5 Control Center"

PLATFORMS: tuple[Platform, ...] = (Platform.SENSOR, Platform.BINARY_SENSOR)

# Legacy command_line/template identities from the pre-native generations.
LEGACY_ENTITIES: dict[str, tuple[str, str]] = {
    "rpi5_cpu_temperature": ("sensor", "command_line"),
    "rpi5_fan_rpm": ("sensor", "command_line"),
    "rpi5_fan_pwm": ("sensor", "command_line"),
    "rpi5_fan_level": ("sensor", "command_line"),
    "rpi5_fan_max_level": ("sensor", "command_line"),
    "rpi5_fan_package_version": ("sensor", "template"),
    "rpi5_fan_percent": ("sensor", "template"),
    "rpi5_cooling_status": ("sensor", "template"),
    "rpi5_cooling_problem": ("binary_sensor", "template"),
    "rpi5_high_temperature": ("binary_sensor", "template"),
    "rpi5_local_package_update_available": ("binary_sensor", "template"),
}
