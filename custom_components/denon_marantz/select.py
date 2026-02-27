from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_ADD_EXTENDED_ENTITIES,
    DEFAULT_ADD_EXTENDED_ENTITIES,
    DEFAULT_INPUT_SOURCES,
    DIALOGUE_ENHANCER_OPTIONS,
    DYNAMIC_COMPRESSION_OPTIONS,
    DYNAMIC_VOLUME_OPTIONS,
    LOUDNESS_OPTIONS,
    DOMAIN,
)
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
    entities: list[SelectEntity] = [
        DenonMarantzInputSourceSelect(entry, coordinator, client),
    ]

    if entry.options.get(CONF_ADD_EXTENDED_ENTITIES, DEFAULT_ADD_EXTENDED_ENTITIES):
        entities.extend(
            [
                DenonMarantzDynamicVolumeSelect(entry, coordinator, client),
                DenonMarantzDialogueEnhancerSelect(entry, coordinator, client),
                DenonMarantzDynamicCompressionSelect(entry, coordinator, client),
                DenonMarantzLoudnessSelect(entry, coordinator, client),
            ]
        )

    async_add_entities(entities)


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
        self._attr_device_info = build_device_info(entry)

    @property
    def options(self) -> list[str]:
        if not self.coordinator.data:
            return DEFAULT_INPUT_SOURCES

        source_options = self.coordinator.data.get("source_options")
        if isinstance(source_options, list) and source_options:
            return source_options

        return DEFAULT_INPUT_SOURCES

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


class DenonMarantzDynamicVolumeSelect(
    CoordinatorEntity[DenonMarantzDataUpdateCoordinator],
    SelectEntity,
):
    _attr_translation_key = "dynamic_volume"

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DenonMarantzDataUpdateCoordinator,
        client: DenonMarantzClient,
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_dynamic_volume"
        self._attr_name = "Dynamic Volume"
        self._attr_options = DYNAMIC_VOLUME_OPTIONS
        self._attr_device_info = build_device_info(entry)

    @property
    def current_option(self) -> str | None:
        if not self.coordinator.data:
            return None

        current = self.coordinator.data.get("dynamic_volume")
        if not current:
            return None

        normalized = str(current).strip().casefold()
        for option in self.options:
            if option.casefold() == normalized:
                return option

        return None

    async def async_select_option(self, option: str) -> None:
        await self._client.async_set_dynamic_volume(option)
        await self.coordinator.async_request_refresh()


class DenonMarantzDialogueEnhancerSelect(
    CoordinatorEntity[DenonMarantzDataUpdateCoordinator],
    SelectEntity,
):
    _attr_translation_key = "dialogue_enhancer"

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DenonMarantzDataUpdateCoordinator,
        client: DenonMarantzClient,
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_dialogue_enhancer"
        self._attr_name = "Dialogue Enhancer"
        self._attr_options = DIALOGUE_ENHANCER_OPTIONS
        self._attr_device_info = build_device_info(entry)

    @property
    def current_option(self) -> str | None:
        if not self.coordinator.data:
            return None

        current = self.coordinator.data.get("dialogue_enhancer")
        if not current:
            return None

        normalized = str(current).strip().casefold()
        for option in self.options:
            if option.casefold() == normalized:
                return option

        return None

    async def async_select_option(self, option: str) -> None:
        await self._client.async_set_dialogue_enhancer(option)
        await self.coordinator.async_request_refresh()


class DenonMarantzDynamicCompressionSelect(
    CoordinatorEntity[DenonMarantzDataUpdateCoordinator],
    SelectEntity,
):
    _attr_translation_key = "dynamic_compression"

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DenonMarantzDataUpdateCoordinator,
        client: DenonMarantzClient,
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_dynamic_compression"
        self._attr_name = "Dynamic Compression"
        self._attr_options = DYNAMIC_COMPRESSION_OPTIONS
        self._attr_device_info = build_device_info(entry)

    @property
    def current_option(self) -> str | None:
        if not self.coordinator.data:
            return None

        current = self.coordinator.data.get("dynamic_compression")
        if not current:
            return None

        normalized = str(current).strip().casefold()
        for option in self.options:
            if option.casefold() == normalized:
                return option

        return None

    async def async_select_option(self, option: str) -> None:
        await self._client.async_set_dynamic_compression(option)
        await self.coordinator.async_request_refresh()


class DenonMarantzLoudnessSelect(
    CoordinatorEntity[DenonMarantzDataUpdateCoordinator],
    SelectEntity,
):
    _attr_translation_key = "loudness"

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DenonMarantzDataUpdateCoordinator,
        client: DenonMarantzClient,
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_loudness"
        self._attr_name = "Loudness"
        self._attr_options = LOUDNESS_OPTIONS
        self._attr_device_info = build_device_info(entry)

    @property
    def current_option(self) -> str | None:
        if not self.coordinator.data:
            return None

        current = self.coordinator.data.get("loudness")
        if not current:
            return None

        normalized = str(current).strip().casefold()
        for option in self.options:
            if option.casefold() == normalized:
                return option

        return None

    async def async_select_option(self, option: str) -> None:
        await self._client.async_set_loudness(option)
        await self.coordinator.async_request_refresh()
