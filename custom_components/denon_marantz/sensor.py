from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_ADD_EXTENDED_ENTITIES,
    DEFAULT_ADD_EXTENDED_ENTITIES,
    DOMAIN,
    STATUS_SENSOR_COMMANDS,
)
from .coordinator import DenonMarantzDataUpdateCoordinator
from .entity import build_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DenonMarantzDataUpdateCoordinator = data["coordinator"]

    entities: list[SensorEntity] = [
        DenonMarantzSoundModeSensor(entry, coordinator),
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
        self._attr_unique_id = f"{entry.entry_id}_sound_mode"
        self._attr_device_info = build_device_info(entry)

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
        self._attr_unique_id = f"{entry.entry_id}_{sensor_key}"
        self._attr_device_info = build_device_info(entry)

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data:
            return None

        status_sensors = self.coordinator.data.get("status_sensors")
        if not isinstance(status_sensors, dict):
            return None

        value = status_sensors.get(self._sensor_key)
        return value if isinstance(value, str) else None
