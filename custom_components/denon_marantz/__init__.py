from __future__ import annotations

import logging
from dataclasses import dataclass, replace

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import (
    ATTR_ALLOW_TIMEOUT,
    ATTR_COMMAND,
    ATTR_ENTRY_ID,
    ATTR_EXPECTED_PREFIXES,
    ATTR_TIMEOUT,
    CONF_ADD_EXTENDED_ENTITIES,
    CONF_INPUT_FILTER,
    DEFAULT_ADD_EXTENDED_ENTITIES,
    DEFAULT_INPUT_FILTER,
    DOMAIN,
    SERVICE_SEND_COMMAND,
)
from .coordinator import DenonMarantzDataUpdateCoordinator
from .denon_protocol import DenonMarantzClient
from .identity import DenonMarantzIdentity, async_probe_identity
from .migration import migrated_unique_id

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
    Platform.SELECT,
    Platform.BUTTON,
    Platform.SENSOR,
    Platform.SWITCH,
]


@dataclass
class DenonMarantzRuntimeData:
    """Runtime data for a Denon/Marantz config entry."""

    client: DenonMarantzClient
    coordinator: DenonMarantzDataUpdateCoordinator
    identity: DenonMarantzIdentity


type DenonMarantzConfigEntry = ConfigEntry[DenonMarantzRuntimeData]

SEND_COMMAND_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_COMMAND): cv.string,
        vol.Optional(ATTR_ENTRY_ID): cv.string,
        vol.Optional(ATTR_TIMEOUT, default=2.0): vol.Coerce(float),
        vol.Optional(ATTR_EXPECTED_PREFIXES, default=[]): vol.All(
            cv.ensure_list,
            [cv.string],
        ),
        vol.Optional(ATTR_ALLOW_TIMEOUT): bool,
    }
)


async def _async_handle_send_command_service(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, str]:
    entries = {
        entry.entry_id: entry.runtime_data
        for entry in hass.config_entries.async_loaded_entries(DOMAIN)
        if hasattr(entry, "runtime_data")
    }

    if not entries:
        raise HomeAssistantError("No Denon Marantz AVR entries are loaded")

    requested_entry_id = call.data.get(ATTR_ENTRY_ID)
    if requested_entry_id:
        selected_entry_id = str(requested_entry_id)
        if selected_entry_id not in entries:
            raise HomeAssistantError(f"Entry '{selected_entry_id}' is not loaded")
    else:
        if len(entries) != 1:
            raise HomeAssistantError("Multiple Denon Marantz AVR entries found; provide entry_id")
        selected_entry_id = next(iter(entries))

    client = entries[selected_entry_id].client

    command = str(call.data[ATTR_COMMAND]).strip()
    if not command:
        raise HomeAssistantError("Service data 'command' must not be empty")

    timeout = float(call.data.get(ATTR_TIMEOUT, 2.0))
    if timeout <= 0:
        raise HomeAssistantError("Service data 'timeout' must be greater than 0")

    expected_prefixes = tuple(
        prefix.strip() for prefix in call.data.get(ATTR_EXPECTED_PREFIXES, []) if prefix.strip()
    )

    allow_timeout_value = call.data.get(ATTR_ALLOW_TIMEOUT)
    if allow_timeout_value is None:
        allow_timeout = not command.endswith("?") and not expected_prefixes
    else:
        allow_timeout = bool(allow_timeout_value)

    response = await client.async_send_command(
        command=command,
        timeout=timeout,
        expected_prefixes=expected_prefixes or None,
        allow_timeout=allow_timeout,
    )

    return {
        "entry_id": selected_entry_id,
        "response": response,
    }


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    if not hass.services.has_service(DOMAIN, SERVICE_SEND_COMMAND):

        async def _handle_send_command_service(call: ServiceCall) -> dict[str, str]:
            return await _async_handle_send_command_service(hass, call)

        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_COMMAND,
            _handle_send_command_service,
            schema=SEND_COMMAND_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )

    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate host- and config-entry-based registry identities."""
    if entry.version >= 2:
        return True

    try:
        identity = await async_probe_identity(entry.data["host"])
    except Exception:  # noqa: BLE001
        _LOGGER.warning(
            "Unable to probe receiver identity while migrating entry %s",
            entry.entry_id,
            exc_info=True,
        )
        identity = None
    if identity is None:
        _LOGGER.warning("No stable receiver identity found for entry %s", entry.entry_id)
        return False

    entity_registry = er.async_get(hass)
    existing_keys = {
        (entity.domain, entity.platform, entity.unique_id)
        for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    }
    collisions: set[str] = set()

    def migrate_entity(entity: er.RegistryEntry) -> dict[str, str] | None:
        new_unique_id = migrated_unique_id(
            entity.domain,
            entity.unique_id,
            entry.entry_id,
            identity.stable_id,
        )
        if new_unique_id is None:
            return None
        if (entity.domain, entity.platform, new_unique_id) in existing_keys:
            collisions.add(entity.entity_id)
            return None
        return {"new_unique_id": new_unique_id}

    await er.async_migrate_entries(hass, entry.entry_id, migrate_entity)
    for entity_id in collisions:
        _LOGGER.info("Removing stale colliding registry entity %s", entity_id)
        entity_registry.async_remove(entity_id)

    device_registry = dr.async_get(hass)
    old_identifier = (DOMAIN, str(entry.data["host"]).lower())
    legacy_device = device_registry.async_get_device_by_identifier(
        old_identifier, entry.entry_id
    )
    current_device = device_registry.async_get_device_by_identifier(
        (DOMAIN, identity.stable_id), entry.entry_id
    )
    if legacy_device is not None and current_device is None:
        device_registry.async_update_device(
            legacy_device.id,
            new_identifiers={(DOMAIN, identity.stable_id)},
        )
    elif (
        legacy_device is not None
        and current_device is not None
        and legacy_device.id != current_device.id
    ):
        for entity in er.async_entries_for_device(
            entity_registry, legacy_device.id, include_disabled_entities=True
        ):
            entity_registry.async_update_entity(entity.entity_id, device_id=current_device.id)
        device_registry.async_remove_device(legacy_device.id)

    hass.config_entries.async_update_entry(
        entry,
        unique_id=identity.stable_id,
        version=2,
    )
    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    config_entry: DenonMarantzConfigEntry,
    device_entry: dr.DeviceEntry,
) -> bool:
    """Allow stale devices to be removed while protecting verified hardware."""
    live: set[tuple[str, str]] = set()
    if config_entry.version >= 2 and config_entry.unique_id:
        live.add((DOMAIN, config_entry.unique_id))
    runtime = getattr(config_entry, "runtime_data", None)
    if runtime is not None:
        live.add((DOMAIN, runtime.identity.stable_id))
    return not (device_entry.identifiers & live)


async def async_setup_entry(hass: HomeAssistant, entry: DenonMarantzConfigEntry) -> bool:
    try:
        identity = await async_probe_identity(entry.data["host"])
    except Exception as err:
        raise ConfigEntryNotReady("Unable to read receiver identity") from err
    if identity is None:
        raise ConfigEntryNotReady("Receiver did not report a stable identity")
    identity = replace(
        identity,
        name=entry.data.get("name") or identity.name,
    )
    client = DenonMarantzClient(
        host=entry.data["host"],
        port=entry.data["port"],
        include_extended_entities=bool(
            entry.options.get(CONF_ADD_EXTENDED_ENTITIES, DEFAULT_ADD_EXTENDED_ENTITIES)
        ),
        input_filter=entry.options.get(CONF_INPUT_FILTER, DEFAULT_INPUT_FILTER),
    )
    coordinator = DenonMarantzDataUpdateCoordinator(hass, client, identity)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = DenonMarantzRuntimeData(client, coordinator, identity)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: DenonMarantzConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.client.disconnect()

    return unloaded
