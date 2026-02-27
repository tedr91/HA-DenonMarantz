from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_ADD_EXTENDED_ENTITIES,
    CONF_INPUT_FILTER,
    DEFAULT_ADD_EXTENDED_ENTITIES,
    DEFAULT_INPUT_FILTER,
    ATTR_COMMAND,
    ATTR_ENTRY_ID,
    ATTR_EXPECTED_PREFIXES,
    ATTR_TIMEOUT,
    DOMAIN,
    SERVICE_SEND_COMMAND,
)
from .coordinator import DenonMarantzDataUpdateCoordinator
from .denon_protocol import DenonMarantzClient

PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
    Platform.SELECT,
    Platform.BUTTON,
    Platform.SENSOR,
    Platform.SWITCH,
]

SEND_COMMAND_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_COMMAND): cv.string,
        vol.Optional(ATTR_ENTRY_ID): cv.string,
        vol.Optional(ATTR_TIMEOUT, default=2.0): vol.Coerce(float),
        vol.Optional(ATTR_EXPECTED_PREFIXES, default=[]): vol.All(
            cv.ensure_list,
            [cv.string],
        ),
    }
)


async def _async_handle_send_command_service(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, str]:
    domain_data: dict = hass.data.get(DOMAIN, {})
    entries = {
        entry_id: entry_data
        for entry_id, entry_data in domain_data.items()
        if isinstance(entry_data, dict) and "client" in entry_data
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
            raise HomeAssistantError(
                "Multiple Denon Marantz AVR entries found; provide entry_id"
            )
        selected_entry_id = next(iter(entries))

    client: DenonMarantzClient = entries[selected_entry_id]["client"]

    command = str(call.data[ATTR_COMMAND]).strip()
    if not command:
        raise HomeAssistantError("Service data 'command' must not be empty")

    timeout = float(call.data.get(ATTR_TIMEOUT, 2.0))
    if timeout <= 0:
        raise HomeAssistantError("Service data 'timeout' must be greater than 0")

    expected_prefixes = tuple(
        prefix.strip() for prefix in call.data.get(ATTR_EXPECTED_PREFIXES, []) if prefix.strip()
    )

    response = await client.async_send_command(
        command=command,
        timeout=timeout,
        expected_prefixes=expected_prefixes or None,
    )

    return {
        "entry_id": selected_entry_id,
        "response": response,
    }


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})

    if not hass.services.has_service(DOMAIN, SERVICE_SEND_COMMAND):
        async def _handle_send_command_service(call: ServiceCall) -> dict[str, str]:
            return await _async_handle_send_command_service(hass, call)

        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_COMMAND,
            _handle_send_command_service,
            schema=SEND_COMMAND_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    client = DenonMarantzClient(
        host=entry.data["host"],
        port=entry.data["port"],
        include_extended_entities=bool(
            entry.options.get(CONF_ADD_EXTENDED_ENTITIES, DEFAULT_ADD_EXTENDED_ENTITIES)
        ),
        input_filter=str(entry.options.get(CONF_INPUT_FILTER, DEFAULT_INPUT_FILTER)),
    )
    coordinator = DenonMarantzDataUpdateCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        client: DenonMarantzClient = entry_data["client"]
        await client.disconnect()

    return unloaded
