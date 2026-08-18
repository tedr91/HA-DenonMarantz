from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_ADD_EXTENDED_ENTITIES,
    DEFAULT_ADD_EXTENDED_ENTITIES,
    STATUS_SENSOR_COMMANDS,
)
from .coordinator import DenonMarantzDataUpdateCoordinator
from .entity import build_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator

    entities: list[SensorEntity] = [
        DenonMarantzSoundModeSensor(entry, coordinator),
        DenonMarantzActiveSpeakersSensor(entry, coordinator),
    ]

    if entry.options.get(CONF_ADD_EXTENDED_ENTITIES, DEFAULT_ADD_EXTENDED_ENTITIES):
        entities.extend(
            [
                DenonMarantzStatusSensor(entry, coordinator, sensor_key)
                for sensor_key, _, _ in STATUS_SENSOR_COMMANDS
            ]
        )

    async_add_entities(entities)


class DenonMarantzSoundModeSensor(
    CoordinatorEntity[DenonMarantzDataUpdateCoordinator],
    SensorEntity,
):
    _attr_has_entity_name = True
    _attr_translation_key = "sound_mode"

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DenonMarantzDataUpdateCoordinator,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.identity.stable_id}_sound_mode"
        self._attr_device_info = build_device_info(coordinator)

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data:
            return None
        value = self.coordinator.data.get("sound_mode")
        return value if isinstance(value, str) else None


class DenonMarantzStatusSensor(
    CoordinatorEntity[DenonMarantzDataUpdateCoordinator],
    SensorEntity,
):
    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DenonMarantzDataUpdateCoordinator,
        sensor_key: str,
    ) -> None:
        super().__init__(coordinator)
        self._sensor_key = sensor_key
        self._attr_translation_key = sensor_key
        self._attr_unique_id = f"{coordinator.identity.stable_id}_{sensor_key}"
        self._attr_device_info = build_device_info(coordinator)

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data:
            return None

        status_sensors = self.coordinator.data.get("status_sensors")
        if not isinstance(status_sensors, dict):
            return None

        value = status_sensors.get(self._sensor_key)
        return value if isinstance(value, str) else None


class DenonMarantzActiveSpeakersSensor(
    CoordinatorEntity[DenonMarantzDataUpdateCoordinator],
    SensorEntity,
):
    _attr_has_entity_name = True
    _attr_translation_key = "active_speakers"

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DenonMarantzDataUpdateCoordinator,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.identity.stable_id}_active_speakers"
        self._attr_device_info = build_device_info(coordinator)

    @property
    def native_value(self) -> str | None:
        speakers = self._active_speakers()
        if not speakers:
            return None
        return ", ".join(speakers)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        speakers = self._active_speakers()
        if speakers is None:
            return None

        codes = self.coordinator.data.get("active_speaker_codes")
        layout = self.coordinator.data.get("speaker_layout")
        return {
            "channels": codes if isinstance(codes, list) else [],
            "speaker_count": len(speakers),
            "layout": layout if isinstance(layout, str) else None,
        }

    def _active_speakers(self) -> list[str] | None:
        if not self.coordinator.data:
            return None

        value = self.coordinator.data.get("active_speakers")
        return value if isinstance(value, list) else None
