from __future__ import annotations

import asyncio
import logging
from typing import Any


class DenonMarantzClient:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__)
        self.supports_zone2 = False
        self.supports_zone3 = False
        self.zone_capabilities: dict[str, dict[str, bool]] = {
            "2": {"volume": False, "mute": False, "source": False},
            "3": {"volume": False, "mute": False, "source": False},
        }
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        if self._writer is not None:
            return
        self._reader, self._writer = await asyncio.open_connection(self.host, self.port)

    async def disconnect(self) -> None:
        if self._writer is None:
            return
        self._writer.close()
        await self._writer.wait_closed()
        self._reader = None
        self._writer = None

    async def _async_send(self, command: str, timeout: float = 2.0) -> str:
        async with self._lock:
            await self.connect()

            assert self._writer is not None
            assert self._reader is not None

            self._writer.write(f"{command}\r".encode("ascii"))
            await self._writer.drain()
            response = await asyncio.wait_for(self._reader.readuntil(b"\r"), timeout=timeout)
            return response.decode("ascii", errors="ignore").strip()

    async def async_detect_zone_support(self) -> None:
        self.supports_zone2 = await self._async_is_zone_supported("Z2?", "Z2")
        self.supports_zone3 = await self._async_is_zone_supported("Z3?", "Z3")

        if self.supports_zone2:
            self.zone_capabilities["2"] = {
                "volume": await self._async_command_supported("Z2VOL?", ("Z2VOL", "Z2")),
                "mute": await self._async_command_supported("Z2MU?", ("Z2MU", "Z2")),
                "source": await self._async_command_supported("Z2?", ("Z2",)),
            }

        if self.supports_zone3:
            self.zone_capabilities["3"] = {
                "volume": await self._async_command_supported("Z3VOL?", ("Z3VOL", "Z3")),
                "mute": await self._async_command_supported("Z3MU?", ("Z3MU", "Z3")),
                "source": await self._async_command_supported("Z3?", ("Z3",)),
            }

    async def _async_command_supported(self, command: str, valid_prefixes: tuple[str, ...]) -> bool:
        try:
            response = await self._async_send(command, timeout=1.5)
        except Exception:
            return False

        response_upper = response.upper()
        if response_upper.startswith("E"):
            return False
        return any(response_upper.startswith(prefix) for prefix in valid_prefixes)

    async def _async_is_zone_supported(self, command: str, prefix: str) -> bool:
        try:
            response = await self._async_send(command, timeout=1.5)
        except Exception:
            return False

        response_upper = response.upper()
        return response_upper.startswith(prefix) and not response_upper.startswith("E")

    async def async_get_status(self) -> dict[str, Any]:
        power = await self._async_send("PW?")
        volume = await self._async_send("MV?")
        source = await self._async_send("SI?")
        mute = await self._async_send("MU?")
        sound_mode = await self._async_send("MS?")

        zone2_power = None
        zone3_power = None
        zone2_volume = None
        zone3_volume = None
        zone2_muted = None
        zone3_muted = None
        zone2_source = None
        zone3_source = None

        if self.supports_zone2:
            try:
                zone2 = await self._async_send("Z2?")
                zone2_power = self._parse_zone_power(zone2, "Z2")
                zone2_source = self._parse_zone_source(zone2, "Z2")
            except Exception:
                zone2_power = None

            if self.zone_capabilities["2"]["volume"]:
                try:
                    zone2_vol = await self._async_send("Z2VOL?")
                    zone2_volume = self._parse_zone_volume(zone2_vol, "Z2VOL")
                except Exception:
                    zone2_volume = None

            if self.zone_capabilities["2"]["mute"]:
                try:
                    zone2_mute = await self._async_send("Z2MU?")
                    zone2_muted = self._parse_zone_mute(zone2_mute, "Z2MU")
                except Exception:
                    zone2_muted = None

        if self.supports_zone3:
            try:
                zone3 = await self._async_send("Z3?")
                zone3_power = self._parse_zone_power(zone3, "Z3")
                zone3_source = self._parse_zone_source(zone3, "Z3")
            except Exception:
                zone3_power = None

            if self.zone_capabilities["3"]["volume"]:
                try:
                    zone3_vol = await self._async_send("Z3VOL?")
                    zone3_volume = self._parse_zone_volume(zone3_vol, "Z3VOL")
                except Exception:
                    zone3_volume = None

            if self.zone_capabilities["3"]["mute"]:
                try:
                    zone3_mute = await self._async_send("Z3MU?")
                    zone3_muted = self._parse_zone_mute(zone3_mute, "Z3MU")
                except Exception:
                    zone3_muted = None

        return {
            "power": power.replace("PW", ""),
            "volume": self._parse_volume(volume),
            "source": source.replace("SI", ""),
            "muted": mute.endswith("ON"),
            "sound_mode": sound_mode.replace("MS", ""),
            "zone2_supported": self.supports_zone2,
            "zone3_supported": self.supports_zone3,
            "zone2_capabilities": self.zone_capabilities["2"],
            "zone3_capabilities": self.zone_capabilities["3"],
            "zone2_power": zone2_power,
            "zone3_power": zone3_power,
            "zone2_volume": zone2_volume,
            "zone3_volume": zone3_volume,
            "zone2_muted": zone2_muted,
            "zone3_muted": zone3_muted,
            "zone2_source": zone2_source,
            "zone3_source": zone3_source,
        }

    async def async_set_power(self, on: bool) -> None:
        await self._async_send("PWON" if on else "PWSTANDBY")

    async def async_volume_up(self) -> None:
        await self._async_send("MVUP")

    async def async_volume_down(self) -> None:
        await self._async_send("MVDOWN")

    async def async_set_volume_level(self, level: float) -> None:
        avr_value = max(0, min(98, int(round(level * 98))))
        await self._async_send(f"MV{avr_value:02d}")

    async def async_set_mute(self, mute: bool) -> None:
        await self._async_send("MUON" if mute else "MUOFF")

    async def async_set_source(self, source: str) -> None:
        await self._async_send(f"SI{source}")

    async def async_set_sound_mode(self, sound_mode: str) -> None:
        command_value = sound_mode.replace(" ", "")
        await self._async_send(f"MS{command_value}")

    async def async_set_zone_power(self, zone: str, on: bool) -> None:
        zone_prefix = "Z2" if zone == "2" else "Z3"
        await self._async_send(f"{zone_prefix}{'ON' if on else 'OFF'}")

    async def async_zone_volume_up(self, zone: str) -> None:
        zone_prefix = "Z2" if zone == "2" else "Z3"
        await self._async_send(f"{zone_prefix}UP")

    async def async_zone_volume_down(self, zone: str) -> None:
        zone_prefix = "Z2" if zone == "2" else "Z3"
        await self._async_send(f"{zone_prefix}DOWN")

    async def async_set_zone_mute(self, zone: str, mute: bool) -> None:
        zone_prefix = "Z2" if zone == "2" else "Z3"
        await self._async_send(f"{zone_prefix}MU{'ON' if mute else 'OFF'}")

    async def async_set_zone_source(self, zone: str, source: str) -> None:
        zone_prefix = "Z2" if zone == "2" else "Z3"
        await self._async_send(f"{zone_prefix}{source}")

    @staticmethod
    def _parse_volume(raw: str) -> float:
        value = raw.replace("MV", "")
        try:
            return max(0.0, min(1.0, int(value[:2]) / 98.0))
        except (TypeError, ValueError, IndexError):
            return 0.0

    @staticmethod
    def _parse_zone_power(raw: str, prefix: str) -> str | None:
        value = raw.upper().replace(prefix, "", 1)
        if value.startswith("ON"):
            return "ON"
        if value.startswith("OFF") or value.startswith("STANDBY"):
            return "OFF"
        return "ON"

    @staticmethod
    def _parse_zone_volume(raw: str, prefix: str) -> float | None:
        value = raw.upper().replace(prefix, "", 1)
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) < 2:
            return None
        try:
            return max(0.0, min(1.0, int(digits[:2]) / 98.0))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_zone_mute(raw: str, prefix: str) -> bool | None:
        value = raw.upper().replace(prefix, "", 1)
        if value.startswith("ON"):
            return True
        if value.startswith("OFF"):
            return False
        return None

    @staticmethod
    def _parse_zone_source(raw: str, prefix: str) -> str | None:
        value = raw.upper().replace(prefix, "", 1).strip()
        if not value:
            return None
        if value.startswith(("ON", "OFF", "STANDBY")):
            return None
        if value[:2].isdigit():
            return None
        return value
