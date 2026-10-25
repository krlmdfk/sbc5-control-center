from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from .const import CONFIG_ENTRY_UNIQUE_ID, DOMAIN


class SBC5ControlCenterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create the single local SBC5 Control Center config entry."""

    VERSION = 1

    async def async_step_import(self, user_input: dict[str, Any] | None = None) -> Any:
        await self.async_set_unique_id(CONFIG_ENTRY_UNIQUE_ID)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="SBC5 Control Center", data={})

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> Any:
        await self.async_set_unique_id(CONFIG_ENTRY_UNIQUE_ID)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="SBC5 Control Center", data={})
