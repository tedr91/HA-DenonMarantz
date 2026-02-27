from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_INPUT_SOURCES, DEFAULT_SOUND_MODES, DOMAIN
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
    async_add_entities(
        [
            DenonMarantzSoundModeSelect(entry, coordinator, client),
            DenonMarantzInputSourceSelect(entry, coordinator, client),
        ]
    )


class DenonMarantzSoundModeSelect(
    CoordinatorEntity[DenonMarantzDataUpdateCoordinator],
    SelectEntity,
):
    _attr_translation_key = "sound_mode"

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DenonMarantzDataUpdateCoordinator,
        client: DenonMarantzClient,
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_sound_mode"
        self._attr_name = "Sound Mode"
        self._attr_options = DEFAULT_SOUND_MODES
        self._attr_device_info = build_device_info(entry)

    @property
    def current_option(self) -> str | None:
        if not self.coordinator.data:
            return None

        current = self.coordinator.data.get("sound_mode")
        if not current:
            return None

        normalized = str(current).strip().upper()
        for option in self.options:
            if option.upper() == normalized:
                return option

        return None

    async def async_select_option(self, option: str) -> None:
        await self._client.async_set_sound_mode(option)
        await self.coordinator.async_request_refresh()


class DenonMarantzInputSourceSelect(
    CoordinatorEntity[DenonMarantzDataUpdateCoordinator],
    SelectEntity,
):
    _attr_translation_key = "input_source"

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DenonMarantzDataUpdateCoordinator,
        client: DenonMarantzClient,
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_input_source"
        self._attr_name = "Input Source"
        self._attr_options = DEFAULT_INPUT_SOURCES
        self._attr_device_info = build_device_info(entry)

    @property
    def current_option(self) -> str | None:
        if not self.coordinator.data:
            return None

        current = self.coordinator.data.get("source")
        if not current:
            return None

        normalized = str(current).strip().upper()
        for option in self.options:
            if option.upper() == normalized:
                return option

        return None

    async def async_select_option(self, option: str) -> None:
        await self._client.async_set_source(option)
        await self.coordinator.async_request_refresh()
