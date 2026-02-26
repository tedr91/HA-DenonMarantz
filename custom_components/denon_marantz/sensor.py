from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DenonMarantzDataUpdateCoordinator
from .entity import build_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DenonMarantzDataUpdateCoordinator = data["coordinator"]

    async_add_entities(
        [
            DenonMarantzDiagnosticSensor(entry, coordinator, "zone2_supported"),
            DenonMarantzDiagnosticSensor(entry, coordinator, "zone3_supported"),
            DenonMarantzDiagnosticSensor(entry, coordinator, "zone2_capabilities"),
            DenonMarantzDiagnosticSensor(entry, coordinator, "zone3_capabilities"),
        ]
    )


class DenonMarantzDiagnosticSensor(
    CoordinatorEntity[DenonMarantzDataUpdateCoordinator],
    SensorEntity,
):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DenonMarantzDataUpdateCoordinator,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = build_device_info(entry)

    @property
    def native_value(self) -> str | bool | None:
        if not self.coordinator.data:
            return None

        value = self.coordinator.data.get(self._key)
        if isinstance(value, dict):
            supported = [name for name, enabled in value.items() if enabled]
            return ",".join(sorted(supported)) if supported else "none"

        if isinstance(value, bool):
            return value

        return None
