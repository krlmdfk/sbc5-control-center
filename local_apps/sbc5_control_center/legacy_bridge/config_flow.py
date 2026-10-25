from __future__ import annotations

from typing import Any
from homeassistant import config_entries

DOMAIN = "sbc5_fan_manager_bridge"


class SBC5LegacyBridgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Compatibility flow used only while migrating a pre-1.9.11 config entry."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> Any:
        return self.async_abort(reason="already_configured")

    async def async_step_import(self, user_input: dict[str, Any] | None = None) -> Any:
        return self.async_abort(reason="already_configured")
