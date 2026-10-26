from __future__ import annotations

from pathlib import Path
import re
from typing import Any
import zipfile

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import SBC5Coordinator
from .entity import SBC5CoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SBC5Coordinator = entry.runtime_data
    async_add_entities([SBC5ControlCenterUpdateEntity(coordinator)])


class SBC5ControlCenterUpdateEntity(SBC5CoordinatorEntity, UpdateEntity):
    _attr_icon = "mdi:update"
    _attr_title = "SBC5 Control Center"

    def __init__(self, coordinator: SBC5Coordinator) -> None:
        super().__init__(coordinator, "sbc5_control_center_native_update", "SBC5 Control Center")

    @property
    def installed_version(self) -> str:
        return self.coordinator.data.app_update.installed_version

    @property
    def latest_version(self) -> str:
        return self.coordinator.data.app_update.latest_version

    @property
    def release_summary(self) -> str | None:
        summary = self.coordinator.data.app_update.summary.strip()
        return summary[:255] if summary else None

    @property
    def release_url(self) -> str | None:
        value = self.coordinator.data.app_update.release_url.strip()
        return value or None

    @property
    def supported_features(self) -> UpdateEntityFeature:
        features = UpdateEntityFeature.RELEASE_NOTES
        update = self.coordinator.data.app_update
        if update.state == "available" and update.source == "local_zip" and update.local_install_supported:
            features |= UpdateEntityFeature.INSTALL
        return features

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        update = self.coordinator.data.app_update
        return {
            "source": update.source,
            "restart_required": update.restart_required,
            "release_date": update.release_date,
            "local_package_file": update.local_package_file,
            "repository": update.repository,
            "changelog_url": update.changelog_url,
            "runtime_app_slug": update.runtime_app_slug,
            "update_scope": update.update_scope,
            "card_ui_installed_version": update.card_ui_installed_version,
            "card_ui_latest_version": update.card_ui_latest_version,
        }

    async def async_install(self, version: str | None, backup: bool, **kwargs: Any) -> None:
        update = self.coordinator.data.app_update
        if update.source != "local_zip" or not update.local_install_supported:
            raise HomeAssistantError(
                "Ta wersja SBC5 Control Centera nie może zostać zainstalowana z lokalnej encji Update."
            )
        if version and version != update.latest_version:
            raise HomeAssistantError(
                f"Dostępna lokalna paczka ma wersję {update.latest_version}, a żądano {version}."
            )

        local_fallbacks = ("local_sbc5_control_center", "local_rpi5_fan_manager")
        runtime_slug = update.runtime_app_slug or ""
        runtime_valid = (
            runtime_slug in local_fallbacks
            or runtime_slug.endswith("_sbc5_control_center")
            or runtime_slug.endswith("_rpi5_fan_manager")
        )
        preferred = runtime_slug if runtime_valid else "local_sbc5_control_center"
        candidates = [preferred, *(slug for slug in local_fallbacks if slug != preferred)]
        last_error: Exception | None = None
        for app_slug in candidates:
            try:
                await self.hass.services.async_call(
                    "hassio",
                    "app_stdin",
                    {
                        "app": app_slug,
                        "input": {"command": "install_local_update"},
                    },
                    blocking=True,
                )
                return
            except HomeAssistantError as err:
                last_error = err

        raise HomeAssistantError(
            "Nie udało się przekazać polecenia instalacji do aktywnego runtime SBC5. "
            f"Sprawdzono: {', '.join(candidates)}. Ostatni błąd: {last_error}"
        )

    async def async_release_notes(self) -> str | None:
        update = self.coordinator.data.app_update
        if update.source == "local_zip" and update.local_package_file:
            notes = await self.hass.async_add_executor_job(
                _read_local_release_notes,
                self.hass.config.path(),
                update.local_package_file,
                update.latest_version,
            )
            if notes:
                return notes
        return update.summary or None


def _read_local_release_notes(config_dir: str, package_path: str, version: str) -> str | None:
    # The add-on sees /homeassistant as /config. The Core process sees the same
    # files below its own configuration directory.
    filename = Path(package_path).name
    candidate = None
    for update_dir in ("sbc5_control_center_updates",):
        direct = Path(config_dir) / update_dir / filename
        processed = Path(config_dir) / update_dir / "processed" / filename
        if direct.is_file():
            candidate = direct
            break
        if processed.is_file():
            candidate = processed
            break
    if candidate is None:
        return None

    try:
        with zipfile.ZipFile(candidate) as archive:
            changelog_name = next(
                (name for name in archive.namelist() if name.endswith("CHANGELOG.md")),
                None,
            )
            if not changelog_name:
                return None
            text = archive.read(changelog_name).decode("utf-8", errors="replace")
    except (OSError, zipfile.BadZipFile, KeyError):
        return None

    pattern = re.compile(
        rf"(?ms)^##\s+{re.escape(version)}(?:\s+[^\n]*)?\n(.*?)(?=^##\s+|\Z)"
    )
    match = pattern.search(text)
    if not match:
        return None
    return f"## {version}\n\n{match.group(1).strip()}"
