from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_INPUT_SOURCES, DOMAIN
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
    async_add_entities([DenonMarantzMediaPlayer(entry, coordinator, client)])


class DenonMarantzMediaPlayer(
    CoordinatorEntity[DenonMarantzDataUpdateCoordinator],
    MediaPlayerEntity,
):
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
    )

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DenonMarantzDataUpdateCoordinator,
        client: DenonMarantzClient,
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._attr_name = entry.data.get(CONF_NAME)
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = build_device_info(entry)

    @property
    def state(self) -> MediaPlayerState:
        power = self.coordinator.data.get("power") if self.coordinator.data else ""
        return MediaPlayerState.ON if power == "ON" else MediaPlayerState.OFF

    @property
    def volume_level(self) -> float | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("volume")

    @property
    def is_volume_muted(self) -> bool | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("muted")

    @property
    def source(self) -> str | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("source")

    @property
    def source_list(self) -> list[str] | None:
        if not self.coordinator.data:
            return DEFAULT_INPUT_SOURCES

        source_options = self.coordinator.data.get("source_options")
        if isinstance(source_options, list) and source_options:
            return source_options

        return DEFAULT_INPUT_SOURCES

    async def async_turn_on(self) -> None:
        await self._client.async_set_power(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        await self._client.async_set_power(False)
        await self.coordinator.async_request_refresh()

    async def async_volume_up(self) -> None:
        await self._client.async_volume_up()
        await self.coordinator.async_request_refresh()

    async def async_volume_down(self) -> None:
        await self._client.async_volume_down()
        await self.coordinator.async_request_refresh()

    async def async_set_volume_level(self, volume: float) -> None:
        await self._client.async_set_volume_level(volume)
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        await self._client.async_set_mute(mute)
        await self.coordinator.async_request_refresh()

    async def async_select_source(self, source: str) -> None:
        await self._client.async_set_source(source)
        await self.coordinator.async_request_refresh()
