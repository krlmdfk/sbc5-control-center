from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.const import CONF_TYPE
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

from .const import APP_VERSION, DOMAIN, LEGACY_DOMAIN, OLDER_LEGACY_DOMAIN, LEGACY_ENTITIES, PLATFORMS
from .coordinator import SBC5Coordinator

_LOGGER = logging.getLogger(__name__)

ISSUE_ID = "restart_required"
SERVICE_SET = "set_restart_required"
SERVICE_CLEAR = "clear_restart_required"
MARKER_RELATIVE = Path("sbc5_control_center") / "restart_required.json"
LEGACY_MIGRATION_MARKER_RELATIVE = Path("sbc5_control_center") / "legacy_bridge_migrated.json"

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

SET_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TYPE): vol.In(["home_assistant", "host"]),
        vol.Optional("reason", default="SBC5 Control Center wymaga ponownego uruchomienia."): cv.string,
        vol.Optional("from_version", default=""): cv.string,
        vol.Optional("to_version", default=""): cv.string,
    }
)


def _marker_path(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(str(MARKER_RELATIVE)))


def _read_marker(hass: HomeAssistant) -> dict[str, Any] | None:
    path = _marker_path(hass)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if data.get("type") not in {"home_assistant", "host"}:
        return None
    return data


def _write_json_path(path: Path, data: dict[str, Any]) -> None:
    """Write a small JSON marker from an executor-backed caller."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_marker(hass: HomeAssistant, data: dict[str, Any]) -> None:
    _write_json_path(_marker_path(hass), data)


def _delete_marker(hass: HomeAssistant) -> None:
    try:
        _marker_path(hass).unlink()
    except FileNotFoundError:
        pass


def _create_issue(hass: HomeAssistant, data: dict[str, Any]) -> None:
    restart_type = data.get("type", "home_assistant")
    target = "Home Assistant" if restart_type == "home_assistant" else "Raspberry Pi 5"
    reason = str(data.get("reason") or "SBC5 Control Center wymaga ponownego uruchomienia.")
    ir.async_create_issue(
        hass,
        DOMAIN,
        ISSUE_ID,
        is_fixable=True,
        is_persistent=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key="restart_required",
        translation_placeholders={"target": target, "reason": reason},
        data=data,
    )


def _delete_issue(hass: HomeAssistant) -> None:
    ir.async_delete_issue(hass, DOMAIN, ISSUE_ID)


def _entry_customizations(entry: er.RegistryEntry) -> dict[str, Any]:
    return {
        "name": entry.name,
        "icon": entry.icon,
        "area_id": entry.area_id,
        "disabled_by": entry.disabled_by,
    }


def _matching_entries(registry: er.EntityRegistry, entity_domain: str, unique_id: str) -> list[er.RegistryEntry]:
    prefix = f"{entity_domain}."
    return [
        entry
        for entry in registry.entities.values()
        if entry.unique_id == unique_id and entry.entity_id.startswith(prefix)
    ]




def _migrate_previous_bridge_registry(hass: HomeAssistant) -> None:
    """Adopt entity ids/customizations from the pre-1.9.11 bridge domain."""
    registry = er.async_get(hass)
    data = hass.data.setdefault(DOMAIN, {})
    overrides: dict[str, str] = data.setdefault("entity_id_overrides", {})
    customizations: dict[str, dict[str, Any]] = data.setdefault("legacy_customizations", {})
    for entry in list(registry.entities.values()):
        if entry.platform != LEGACY_DOMAIN:
            continue
        overrides[entry.unique_id] = entry.entity_id
        customizations[entry.entity_id] = _entry_customizations(entry)
        _LOGGER.info("Migrating SBC5 entity %s from %s to %s", entry.entity_id, LEGACY_DOMAIN, DOMAIN)
        registry.async_remove(entry.entity_id)


async def _cleanup_previous_bridge_entry(hass: HomeAssistant) -> None:
    """Remove the old config entry only after the canonical bridge is healthy."""
    await asyncio.sleep(5)
    failed = False
    for old_entry in list(hass.config_entries.async_entries(LEGACY_DOMAIN)):
        try:
            await hass.config_entries.async_remove(old_entry.entry_id)
            _LOGGER.info("Removed legacy SBC5 bridge config entry %s", old_entry.entry_id)
        except Exception:  # migration must never block the new integration
            failed = True
            _LOGGER.exception("Could not remove legacy SBC5 bridge config entry")
    remaining = list(hass.config_entries.async_entries(LEGACY_DOMAIN))
    if not failed and not remaining:
        marker = Path(hass.config.path(str(LEGACY_MIGRATION_MARKER_RELATIVE)))
        try:
            await hass.async_add_executor_job(
                _write_json_path,
                marker,
                {"migrated": True, "from_domain": LEGACY_DOMAIN, "to_domain": DOMAIN, "version": APP_VERSION},
            )
        except OSError:
            _LOGGER.warning("Could not write legacy bridge migration marker")


def _migrate_legacy_entity_registry(hass: HomeAssistant) -> None:
    """Move known command_line/template identities back to the native bridge.

    This migration is intentionally based on exact unique_id matches so it also
    repairs *_2 collisions left by 1.6.0-1.6.3. The canonical entity_id and user
    customizations are preserved whenever possible.
    """
    registry = er.async_get(hass)
    data = hass.data.setdefault(DOMAIN, {})
    overrides: dict[str, str] = dict(data.get("entity_id_overrides", {}))
    customizations: dict[str, dict[str, Any]] = dict(data.get("legacy_customizations", {}))

    for unique_id, (entity_domain, legacy_platform) in LEGACY_ENTITIES.items():
        canonical = f"{entity_domain}.{unique_id}"
        entries = _matching_entries(registry, entity_domain, unique_id)
        native_entries = [entry for entry in entries if entry.platform == DOMAIN]
        legacy_entries = [entry for entry in entries if entry.platform == legacy_platform]
        native = next((entry for entry in native_entries if entry.entity_id == canonical), None)
        if native is None and native_entries:
            native = native_entries[0]

        desired_id = canonical
        owner = registry.async_get(canonical)
        if owner is not None and owner.unique_id != unique_id:
            desired_id = native.entity_id if native is not None else (legacy_entries[0].entity_id if legacy_entries else canonical)

        source = next((entry for entry in legacy_entries if entry.entity_id == canonical), None)
        if source is None and legacy_entries:
            source = legacy_entries[0]
        if source is not None:
            customizations[desired_id] = _entry_customizations(source)

        # Keep at most one native entry.
        for extra in native_entries:
            if native is not None and extra.entity_id == native.entity_id:
                continue
            _LOGGER.warning("Removing duplicate native SBC5 entity %s", extra.entity_id)
            registry.async_remove(extra.entity_id)

        for entry in legacy_entries:
            _LOGGER.info("Removing legacy SBC5 entity %s (%s/%s)", entry.entity_id, entry.platform, unique_id)
            registry.async_remove(entry.entity_id)

        if native is not None:
            if native.entity_id != desired_id and registry.async_get(desired_id) is None:
                old_id = native.entity_id
                registry.async_update_entity(old_id, new_entity_id=desired_id)
                _LOGGER.info("Restored native SBC5 entity_id %s -> %s", old_id, desired_id)
        else:
            overrides[unique_id] = desired_id

    data = hass.data.setdefault(DOMAIN, {})
    data["entity_id_overrides"] = overrides
    data["legacy_customizations"] = customizations


def _canonicalize_native_entity_registry(hass: HomeAssistant) -> None:
    """Restore stable canonical entity_ids for native 1.7.x entities.

    Home Assistant normally derives an object_id from the display name on first
    registration.  That made names such as ``SBC5 CPU / Overclock Status`` become
    ``sensor.sbc5_cpu_overclock_status`` while the dashboard contract expects
    ``sensor.sbc5_overclock_status``.  v1.7.10 repairs already-created registry
    entries before platforms are forwarded and removes duplicate native records
    for the same unique_id.
    """

    registry = er.async_get(hass)
    # Only canonicalize entities introduced by the 1.7.x native telemetry layer.
    # Older fan/cooling entities may have deliberate user-renamed entity_ids and
    # are handled by the legacy migration above, which preserves customization.
    canonical: dict[str, str] = {
        "sbc5_cpu_frequency": "sensor",
        "sbc5_usb_current_limit": "sensor",
        "sbc5_input_voltage": "sensor",
        "sbc5_pmic_power": "sensor",
        "sbc5_pmic_equivalent_current": "sensor",
        "sbc5_pmic_temperature": "sensor",
        "sbc5_core_current": "sensor",
        "sbc5_core_voltage": "sensor",
        "sbc5_core_power": "sensor",
        "sbc5_usb_declared_current": "sensor",
        "sbc5_usb_device_count": "sensor",
        "sbc5_power_supply": "sensor",
        "sbc5_boot_configuration": "sensor",
        "sbc5_overclock_status": "sensor",
        "sbc5_config_pending_restart": "binary_sensor",
    }

    for unique_id, entity_domain in canonical.items():
        matches = [
            entry
            for entry in registry.entities.values()
            if entry.platform == DOMAIN
            and entry.unique_id == unique_id
            and entry.entity_id.startswith(f"{entity_domain}.")
        ]
        if not matches:
            continue

        target = f"{entity_domain}.{unique_id}"
        target_owner = registry.async_get(target)
        primary = next((entry for entry in matches if entry.entity_id == target), matches[0])

        if target_owner is None and primary.entity_id != target:
            old_id = primary.entity_id
            registry.async_update_entity(old_id, new_entity_id=target)
            _LOGGER.info("Canonicalized SBC5 entity_id %s -> %s", old_id, target)
            primary = registry.async_get(target) or primary
        elif target_owner is not None and not (
            target_owner.platform == DOMAIN and target_owner.unique_id == unique_id
        ):
            _LOGGER.warning(
                "Cannot canonicalize SBC5 entity %s because %s is owned by another entity",
                unique_id,
                target,
            )

        keep_id = target if registry.async_get(target) is not None and registry.async_get(target).unique_id == unique_id else primary.entity_id
        for entry in list(matches):
            if entry.entity_id == keep_id:
                continue
            current = registry.async_get(entry.entity_id)
            if current is not None and current.platform == DOMAIN and current.unique_id == unique_id:
                _LOGGER.warning("Removing duplicate native SBC5 entity %s", entry.entity_id)
                registry.async_remove(entry.entity_id)


def _remove_deprecated_native_update_entity(hass: HomeAssistant) -> None:
    """Remove the duplicate custom Update entity introduced in 1.6.x/1.7.0.

    The Supervisor app itself already owns the canonical update entry shown in
    Settings > Updates. Local ZIP installation remains available through the
    package scripts and dashboard, so keeping a second UpdateEntity only
    duplicates the same product in the UI.
    """
    registry = er.async_get(hass)
    for entry in list(registry.entities.values()):
        if (
            entry.entity_id.startswith("update.")
            and entry.platform == DOMAIN
            and entry.unique_id == "sbc5_fan_manager_native_update"
        ):
            _LOGGER.info("Removing deprecated duplicate SBC5 update entity %s", entry.entity_id)
            registry.async_remove(entry.entity_id)


def _restore_legacy_customizations(hass: HomeAssistant) -> None:
    registry = er.async_get(hass)
    customizations: dict[str, dict[str, Any]] = hass.data.get(DOMAIN, {}).get(
        "legacy_customizations", {}
    )
    for entity_id, old in customizations.items():
        entry = registry.async_get(entity_id)
        if entry is None or entry.platform != DOMAIN:
            continue
        changes: dict[str, Any] = {}
        if old.get("name") is not None:
            changes["name"] = old["name"]
        if old.get("icon") is not None:
            changes["icon"] = old["icon"]
        if old.get("area_id") is not None:
            changes["area_id"] = old["area_id"]
        if old.get("disabled_by") is not None:
            changes["disabled_by"] = old["disabled_by"]
        if changes:
            registry.async_update_entity(entity_id, **changes)



def _sbc5_namespace_target_id(entity_id: str) -> str:
    domain, _, object_id = entity_id.partition(".")
    if object_id.startswith("rpi5_"):
        object_id = "sbc5_" + object_id[len("rpi5_"):]
    if object_id == "sbc5_fan_manager_update":
        object_id = "sbc5_control_center_update"
    elif object_id == "sbc5_fan_manager_host_telemetry":
        object_id = "sbc5_control_center_host_telemetry"
    elif object_id == "sbc5_fan_package_version":
        object_id = "sbc5_package_version"
    elif object_id == "sbc5_fan_restart_required":
        object_id = "sbc5_restart_required"
    return f"{domain}.{object_id}" if domain else object_id


async def _prepare_sbc5_namespace_registry(hass: HomeAssistant) -> None:
    """Capture customization from legacy RPi5 registry entries and free old IDs.

    The new integration gets new sbc5_* unique/entity IDs. Old rpi5_* IDs are
    later recreated by the legacy compatibility package as forwarding aliases.
    """
    registry = er.async_get(hass)
    data = hass.data.setdefault(DOMAIN, {})
    overrides: dict[str, str] = data.setdefault("entity_id_overrides", {})
    customizations: dict[str, dict[str, Any]] = data.setdefault("legacy_customizations", {})
    removed: list[dict[str, str]] = []
    for old in list(registry.entities.values()):
        if old.platform not in {LEGACY_DOMAIN, OLDER_LEGACY_DOMAIN}:
            continue
        target_eid = _sbc5_namespace_target_id(old.entity_id)
        old_uid = str(old.unique_id or "")
        new_uid = old_uid
        if new_uid.startswith("rpi5_"):
            new_uid = "sbc5_" + new_uid[len("rpi5_"):]
        if new_uid == "sbc5_fan_manager_native_update":
            new_uid = "sbc5_control_center_native_update"
        overrides[new_uid] = target_eid
        customizations[target_eid] = _entry_customizations(old)
        removed.append({"entity_id": old.entity_id, "target": target_eid, "unique_id": old_uid})
        # Keep the legacy entity registered until native SBC5 entities are healthy.
        # Removing it here made a failed setup destructive; cleanup is deferred.
    marker = Path(hass.config.path("sbc5_control_center", "migration", "registry_prepared.json"))
    try:
        await hass.async_add_executor_job(
            _write_json_path,
            marker,
            {"version": APP_VERSION, "removed": removed},
        )
    except OSError:
        _LOGGER.warning("Could not write SBC5 registry migration marker")


async def _cleanup_rpi5_namespace_entries(hass: HomeAssistant) -> None:
    """Remove old-domain config entries only after native SBC5 entities are healthy."""
    healthy = False
    required = ("sensor.sbc5_cpu_temperature", "sensor.sbc5_fan_rpm", "sensor.sbc5_control_center_update")
    for _ in range(45):
        states = [hass.states.get(entity_id) for entity_id in required]
        if all(st is not None and st.state not in {"unknown", "unavailable", "none", ""} for st in states):
            healthy = True
            break
        await asyncio.sleep(2)
    failed = not healthy
    removed: list[str] = []
    if not healthy:
        _LOGGER.warning("SBC5 namespace migration: native entities are not healthy; keeping legacy config entries")
    if healthy:
      for old_domain in (LEGACY_DOMAIN, OLDER_LEGACY_DOMAIN):
        for old_entry in list(hass.config_entries.async_entries(old_domain)):
          try:
            await hass.config_entries.async_remove(old_entry.entry_id)
            removed.append(old_entry.entry_id)
          except Exception:
            failed = True
            _LOGGER.exception("Could not remove legacy namespace config entry %s", old_entry.entry_id)
      # Now that native SBC5 telemetry is proven healthy, free any stale legacy
      # registry rows so the compatibility package can own rpi5_* aliases.
      registry = er.async_get(hass)
      for reg_entry in list(registry.entities.values()):
        if reg_entry.platform in {LEGACY_DOMAIN, OLDER_LEGACY_DOMAIN}:
          try:
            registry.async_remove(reg_entry.entity_id)
          except Exception:
            _LOGGER.exception("Could not remove legacy registry entity %s", reg_entry.entity_id)
    marker = Path(hass.config.path("sbc5_control_center", "migration", "integration_ready.json"))
    try:
        await hass.async_add_executor_job(
            _write_json_path,
            marker,
            {"version": APP_VERSION, "ready": not failed, "removed_entries": removed},
        )
    except OSError:
        _LOGGER.debug("Could not write SBC5 integration-ready migration marker")

async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up services, Repairs and bootstrap the single config entry."""

    async def _handle_set(call: ServiceCall) -> None:
        data = dict(call.data)
        await hass.async_add_executor_job(_write_marker, hass, data)
        _create_issue(hass, data)

    async def _handle_clear(call: ServiceCall) -> None:
        await hass.async_add_executor_job(_delete_marker, hass)
        _delete_issue(hass)

    if not hass.services.has_service(DOMAIN, SERVICE_SET):
        hass.services.async_register(DOMAIN, SERVICE_SET, _handle_set, schema=SET_SCHEMA)
    if not hass.services.has_service(DOMAIN, SERVICE_CLEAR):
        hass.services.async_register(DOMAIN, SERVICE_CLEAR, _handle_clear)

    marker = await hass.async_add_executor_job(_read_marker, hass)
    if marker is not None:
        _create_issue(hass, marker)

    if DOMAIN in config and not hass.config_entries.async_entries(DOMAIN):
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data={},
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up native derived telemetry/update entities."""
    _remove_deprecated_native_update_entity(hass)
    await _prepare_sbc5_namespace_registry(hass)
    _canonicalize_native_entity_registry(hass)

    coordinator = SBC5Coordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def _restore_after_registration() -> None:
        await asyncio.sleep(1)
        _restore_legacy_customizations(hass)

    entry.async_create_background_task(
        hass,
        _restore_after_registration(),
        "sbc5_control_center_restore_legacy_customizations",
    )
    entry.async_create_background_task(
        hass, _cleanup_rpi5_namespace_entries(hass), "sbc5_control_center_cleanup_rpi5_namespace"
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the native platforms."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
