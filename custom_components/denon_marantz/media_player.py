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
    entities: list[MediaPlayerEntity] = [DenonMarantzMediaPlayer(entry, coordinator, client)]

    if coordinator.data and coordinator.data.get("zone2_supported"):
        entities.append(DenonMarantzZoneMediaPlayer(entry, coordinator, client, zone="2"))

    if coordinator.data and coordinator.data.get("zone3_supported"):
        entities.append(DenonMarantzZoneMediaPlayer(entry, coordinator, client, zone="3"))

    async_add_entities(entities)


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

    _attr_source_list = ["CD", "TV", "SAT/CBL", "GAME", "AUX", "BLUETOOTH", "TUNER"]

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


class DenonMarantzZoneMediaPlayer(
    CoordinatorEntity[DenonMarantzDataUpdateCoordinator],
    MediaPlayerEntity,
):
    _attr_source_list = ["CD", "TV", "SAT/CBL", "GAME", "AUX", "BLUETOOTH", "TUNER"]

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DenonMarantzDataUpdateCoordinator,
        client: DenonMarantzClient,
        zone: str,
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._zone = zone
        base_name = entry.data.get(CONF_NAME)
        self._attr_name = f"{base_name} Zone {zone}"
        self._attr_unique_id = f"{entry.entry_id}_zone_{zone}"
        self._attr_device_info = build_device_info(entry)

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        features = MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF
        if not self.coordinator.data:
            return features

        caps_key = "zone2_capabilities" if self._zone == "2" else "zone3_capabilities"
        caps = self.coordinator.data.get(caps_key) or {}

        if caps.get("volume"):
            features |= MediaPlayerEntityFeature.VOLUME_STEP
        if caps.get("mute"):
            features |= MediaPlayerEntityFeature.VOLUME_MUTE
        if caps.get("source"):
            features |= MediaPlayerEntityFeature.SELECT_SOURCE

        return features

    @property
    def state(self) -> MediaPlayerState:
        if not self.coordinator.data:
            return MediaPlayerState.OFF

        zone_key = "zone2_power" if self._zone == "2" else "zone3_power"
        zone_power = self.coordinator.data.get(zone_key)
        return MediaPlayerState.ON if zone_power == "ON" else MediaPlayerState.OFF

    @property
    def volume_level(self) -> float | None:
        if not self.coordinator.data:
            return None
        zone_key = "zone2_volume" if self._zone == "2" else "zone3_volume"
        return self.coordinator.data.get(zone_key)

    @property
    def is_volume_muted(self) -> bool | None:
        if not self.coordinator.data:
            return None
        zone_key = "zone2_muted" if self._zone == "2" else "zone3_muted"
        return self.coordinator.data.get(zone_key)

    @property
    def source(self) -> str | None:
        if not self.coordinator.data:
            return None
        zone_key = "zone2_source" if self._zone == "2" else "zone3_source"
        return self.coordinator.data.get(zone_key)

    async def async_turn_on(self) -> None:
        await self._client.async_set_zone_power(self._zone, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        await self._client.async_set_zone_power(self._zone, False)
        await self.coordinator.async_request_refresh()

    async def async_volume_up(self) -> None:
        await self._client.async_zone_volume_up(self._zone)
        await self.coordinator.async_request_refresh()

    async def async_volume_down(self) -> None:
        await self._client.async_zone_volume_down(self._zone)
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        await self._client.async_set_zone_mute(self._zone, mute)
        await self.coordinator.async_request_refresh()

    async def async_select_source(self, source: str) -> None:
        await self._client.async_set_zone_source(self._zone, source)
        await self.coordinator.async_request_refresh()
