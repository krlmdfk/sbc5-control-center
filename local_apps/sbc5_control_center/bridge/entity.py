from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import APP_VERSION, DEVICE_IDENTIFIER, DEVICE_NAME, DOMAIN, LEGACY_DOMAIN
from .coordinator import SBC5Coordinator


def _split_rpi_model(value: str) -> tuple[str, str]:
    """Return a clean model name and hardware revision from DT model text."""
    text = (value or "").strip()
    if not text or text == "N/D":
        return "Raspberry Pi 5", ""
    marker = " Rev "
    if marker in text:
        model, rev = text.rsplit(marker, 1)
        return model.strip(), f"Rev {rev.strip()}"
    return text, ""


def _valid_mac(value: str) -> bool:
    parts = (value or "").strip().lower().split(":")
    return len(parts) == 6 and all(len(part) == 2 and all(ch in "0123456789abcdef" for ch in part) for part in parts)


class SBC5CoordinatorEntity(CoordinatorEntity[SBC5Coordinator]):
    """Base entity for SBC5 Control Center."""

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: SBC5Coordinator,
        unique_id: str,
        name: str,
        entity_id_override: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = unique_id
        self._attr_name = name
        # v1.7.10: wymuś stabilny object_id dla nowych encji, niezależnie od
        # lokalizacji/nazwy wyświetlanej i zmian algorytmu slugowania HA.
        self._attr_suggested_object_id = unique_id
        telemetry = getattr(getattr(coordinator, "data", None), "telemetry", None)
        model, model_hw = _split_rpi_model(getattr(telemetry, "rpi_model", ""))
        hw_version = getattr(telemetry, "hardware_revision", "") or model_hw
        info = DeviceInfo(
            identifiers={(DOMAIN, DEVICE_IDENTIFIER), (LEGACY_DOMAIN, DEVICE_IDENTIFIER)},
            name=DEVICE_NAME,
            manufacturer="Raspberry Pi",
            model=model,
            sw_version=APP_VERSION,
        )
        if telemetry is not None:
            if model_id := (getattr(telemetry, "board_revision", "") or "").strip():
                info["model_id"] = model_id.upper()
            if hw_version:
                info["hw_version"] = hw_version
            if serial := (getattr(telemetry, "serial_number", "") or "").strip():
                info["serial_number"] = serial
            mac = (getattr(telemetry, "network_mac", "") or "").strip().lower()
            if _valid_mac(mac):
                info["connections"] = {(CONNECTION_NETWORK_MAC, mac)}
        self._attr_device_info = info
        if entity_id_override:
            # Home Assistant allows an integration to suggest an entity_id as long as
            # its domain matches the entity platform. This preserves user-renamed IDs
            # during the 1.6 migration from command_line/template.
            self.entity_id = entity_id_override
