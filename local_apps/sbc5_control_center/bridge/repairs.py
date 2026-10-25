from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from . import DOMAIN, ISSUE_ID, MARKER_RELATIVE


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, Any] | None,
) -> RepairsFlow:
    """Create the repair flow for a pending restart."""
    return RestartRepairFlow()


class RestartRepairFlow(RepairsFlow):
    """Native Home Assistant repair flow used to confirm a restart."""

    def _marker_path(self) -> Path:
        return Path(self.hass.config.path(str(MARKER_RELATIVE)))

    def _read_marker(self) -> dict[str, Any]:
        try:
            return json.loads(self._marker_path().read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"type": "home_assistant", "reason": "SBC5 Control Center wymaga ponownego uruchomienia."}

    def _clear(self) -> None:
        ir.async_delete_issue(self.hass, DOMAIN, ISSUE_ID)
        try:
            self._marker_path().unlink()
        except FileNotFoundError:
            pass

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> dict:
        marker = self._read_marker()
        restart_type = marker.get("type", "home_assistant")
        target = "Home Assistant" if restart_type == "home_assistant" else "Raspberry Pi 5"
        reason = str(marker.get("reason") or "SBC5 Control Center wymaga ponownego uruchomienia.")

        if user_input is not None:
            if not user_input.get("confirm", False):
                return self.async_show_form(
                    step_id="init",
                    data_schema=vol.Schema({vol.Required("confirm", default=False): bool}),
                    errors={"base": "confirm_required"},
                    description_placeholders={"target": target, "reason": reason},
                )

            self._clear()
            if restart_type == "host":
                self.hass.async_create_task(
                    self.hass.services.async_call("hassio", "host_reboot", {}, blocking=False)
                )
            else:
                self.hass.async_create_task(
                    self.hass.services.async_call("homeassistant", "restart", {}, blocking=False)
                )
            return self.async_create_entry(data={})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({vol.Required("confirm", default=False): bool}),
            description_placeholders={"target": target, "reason": reason},
        )
