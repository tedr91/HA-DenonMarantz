from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DenonMarantzDataUpdateCoordinator


class DenonMarantzEntity(CoordinatorEntity[DenonMarantzDataUpdateCoordinator]):
    """Base class for Denon/Marantz entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DenonMarantzDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        identity = coordinator.identity
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, identity.stable_id)},
            name=identity.name or None,
            manufacturer=identity.manufacturer,
            model=identity.model,
            serial_number=identity.serial,
            configuration_url=f"http://{coordinator.client.host}",
        )


def build_device_info(
    coordinator: DenonMarantzDataUpdateCoordinator,
) -> DeviceInfo:
    """Build shared device metadata for existing platform entities."""
    identity = coordinator.identity
    return DeviceInfo(
        identifiers={(DOMAIN, identity.stable_id)},
        name=identity.name or None,
        manufacturer=identity.manufacturer,
        model=identity.model,
        serial_number=identity.serial,
        configuration_url=f"http://{coordinator.client.host}",
    )
