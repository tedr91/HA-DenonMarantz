from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ADD_EXTENDED_ENTITIES, DEFAULT_ADD_EXTENDED_ENTITIES, DOMAIN
from .coordinator import DenonMarantzDataUpdateCoordinator
from .denon_protocol import DenonMarantzClient
from .entity import build_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    if not entry.options.get(CONF_ADD_EXTENDED_ENTITIES, DEFAULT_ADD_EXTENDED_ENTITIES):
        return

    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DenonMarantzDataUpdateCoordinator = data["coordinator"]
    client: DenonMarantzClient = data["client"]

    async_add_entities([DenonMarantzDynamicEqSwitch(entry, coordinator, client)])


class DenonMarantzDynamicEqSwitch(
    CoordinatorEntity[DenonMarantzDataUpdateCoordinator],
    SwitchEntity,
):
    _attr_has_entity_name = True
    _attr_translation_key = "dynamic_eq"

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DenonMarantzDataUpdateCoordinator,
        client: DenonMarantzClient,
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_dynamic_eq"
        self._attr_device_info = build_device_info(entry)

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None

        value = self.coordinator.data.get("dynamic_eq")
        return value if isinstance(value, bool) else None

    async def async_turn_on(self, **kwargs) -> None:
        await self._client.async_set_dynamic_eq(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self._client.async_set_dynamic_eq(False)
        await self.coordinator.async_request_refresh()
