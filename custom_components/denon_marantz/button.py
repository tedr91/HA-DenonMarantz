from __future__ import annotations

from collections.abc import Awaitable, Callable

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DenonMarantzDataUpdateCoordinator
from .denon_protocol import DenonMarantzClient
from .entity import build_device_info

ControlAction = Callable[[], Awaitable[None]]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DenonMarantzDataUpdateCoordinator = data["coordinator"]
    client: DenonMarantzClient = data["client"]

    async_add_entities(
        [
            DenonMarantzControlButton(entry, coordinator, "control_up", client.async_cursor_up),
            DenonMarantzControlButton(entry, coordinator, "control_down", client.async_cursor_down),
            DenonMarantzControlButton(entry, coordinator, "control_left", client.async_cursor_left),
            DenonMarantzControlButton(entry, coordinator, "control_right", client.async_cursor_right),
            DenonMarantzControlButton(entry, coordinator, "control_enter", client.async_enter),
            DenonMarantzControlButton(entry, coordinator, "control_back", client.async_return),
            DenonMarantzControlButton(entry, coordinator, "option", client.async_option),
            DenonMarantzControlButton(entry, coordinator, "control_info", client.async_info),
            DenonMarantzControlButton(entry, coordinator, "control_menu", client.async_menu),
        ]
    )


class DenonMarantzControlButton(
    CoordinatorEntity[DenonMarantzDataUpdateCoordinator],
    ButtonEntity,
):
    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DenonMarantzDataUpdateCoordinator,
        translation_key: str,
        action: ControlAction,
    ) -> None:
        super().__init__(coordinator)
        self._action = action
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{entry.entry_id}_{translation_key}"
        self._attr_device_info = build_device_info(entry)

    async def async_press(self) -> None:
        await self._action()
