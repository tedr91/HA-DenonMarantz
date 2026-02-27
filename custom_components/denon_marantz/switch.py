from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DenonMarantzDataUpdateCoordinator
from .denon_protocol import DenonMarantzClient
from .entity import build_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DenonMarantzDataUpdateCoordinator = data["coordinator"]
    client: DenonMarantzClient = data["client"]

    async_add_entities([DenonMarantzMuteSwitch(entry, coordinator, client)])


class DenonMarantzMuteSwitch(
    CoordinatorEntity[DenonMarantzDataUpdateCoordinator],
    SwitchEntity,
):
    _attr_has_entity_name = True
    _attr_translation_key = "mute"

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DenonMarantzDataUpdateCoordinator,
        client: DenonMarantzClient,
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_mute"
        self._attr_device_info = build_device_info(entry)

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data and self.coordinator.data.get("muted"))

    async def async_turn_on(self, **kwargs) -> None:
        await self._client.async_set_mute(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self._client.async_set_mute(False)
        await self.coordinator.async_request_refresh()
