from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .denon_protocol import DenonMarantzClient


class DenonMarantzDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, client: DenonMarantzClient) -> None:
        super().__init__(
            hass,
            logger=client.logger,
            name=DOMAIN,
            update_interval=timedelta(seconds=5),
        )
        self.client = client
        self._last_successful_data: dict[str, Any] | None = None
        self._consecutive_failures = 0

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.client.async_get_status()
            self._last_successful_data = data
            self._consecutive_failures = 0
            return data
        except Exception as err:
            self._consecutive_failures += 1
            if self._last_successful_data is not None:
                self.logger.warning(
                    "AVR update failed (%s). Returning cached state after %s consecutive failure(s).",
                    err,
                    self._consecutive_failures,
                )
                return self._last_successful_data
            raise UpdateFailed(f"Failed to fetch AVR state: {err}") from err
