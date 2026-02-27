from __future__ import annotations

import asyncio
import logging
from typing import Any

from .const import DEFAULT_INPUT_SOURCES


class DenonMarantzClient:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__)
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()
        self._source_code_to_label: dict[str, str] = {}
        self._source_label_to_code: dict[str, str] = {}
        self._source_map_fetched = False

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

    async def _async_reset_connection(self) -> None:
        writer = self._writer
        self._reader = None
        self._writer = None
        if writer is None:
            return
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            return

    async def _async_send(
        self,
        command: str,
        timeout: float = 2.0,
        expected_prefixes: tuple[str, ...] | None = None,
        allow_timeout: bool = False,
    ) -> str:
        async with self._lock:
            expected = tuple(
                prefix.upper() for prefix in (expected_prefixes or self._expected_prefixes(command))
            )

            last_error: Exception | None = None
            for attempt in (1, 2):
                try:
                    await self.connect()
                    return await self._async_send_once(
                        command,
                        timeout,
                        expected,
                        allow_timeout=allow_timeout,
                    )
                except (ConnectionError, OSError, asyncio.IncompleteReadError) as err:
                    last_error = err
                    await self._async_reset_connection()
                    if attempt == 1:
                        self.logger.debug(
                            "Transient AVR connection error on %s; retrying once: %s",
                            command,
                            err,
                        )
                        continue
                    raise

            if last_error is not None:
                raise last_error

            raise RuntimeError("Unexpected protocol send state")

    async def _async_send_once(
        self,
        command: str,
        timeout: float,
        expected: tuple[str, ...],
        allow_timeout: bool,
    ) -> str:
        assert self._writer is not None
        assert self._reader is not None

        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout

        self._writer.write(f"{command}\r".encode("ascii"))
        await self._writer.drain()
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                if allow_timeout:
                    self.logger.debug(
                        "No immediate AVR response for %s; continuing without acknowledgement",
                        command,
                    )
                    return ""
                raise TimeoutError(f"Timeout waiting for response to '{command}'")

            response = await asyncio.wait_for(self._reader.readuntil(b"\r"), timeout=remaining)
            decoded = response.decode("ascii", errors="ignore").strip()
            upper = decoded.upper()

            if upper.startswith("E"):
                return decoded

            if any(upper.startswith(prefix) for prefix in expected):
                return decoded

            self.logger.debug(
                "Discarding unsolicited AVR line while waiting for %s: %s",
                command,
                decoded,
            )

    @staticmethod
    def _expected_prefixes(command: str) -> tuple[str, ...]:
        cmd = command.strip().upper()
        if cmd.endswith("?"):
            cmd = cmd[:-1]

        if cmd.startswith("PW"):
            return ("PW",)
        if cmd.startswith("MV"):
            return ("MV",)
        if cmd.startswith("MU"):
            return ("MU",)
        if cmd.startswith("SI"):
            return ("SI",)
        if cmd.startswith("MS"):
            return ("MS",)

        return (cmd[:2],)

    async def async_get_status(self) -> dict[str, Any]:
        await self._async_ensure_source_map()

        power_raw = await self._async_send("PW?")
        power = self._parse_power(power_raw)

        if power != "ON":
            return {
                "power": power,
                "volume": 0.0,
                "source": None,
                "muted": False,
                "sound_mode": None,
            }

        volume_raw = await self._async_query_optional("MV?")
        source_raw = await self._async_query_optional("SI?")
        mute_raw = await self._async_query_optional("MU?")
        sound_mode_raw = await self._async_query_optional("MS?")

        source_code = self._strip_prefix(source_raw, "SI")
        source_label = self._source_label_from_code(source_code)

        return {
            "power": power,
            "volume": self._parse_volume(volume_raw or ""),
            "source": source_label,
            "source_options": self._source_options(source_label),
            "muted": bool(mute_raw and mute_raw.upper().endswith("ON")),
            "sound_mode": self._strip_prefix(sound_mode_raw, "MS"),
        }

    async def _async_ensure_source_map(self) -> None:
        if self._source_map_fetched:
            return

        self._source_map_fetched = True
        discovered = await self._async_fetch_source_map()
        if discovered:
            self._source_code_to_label = discovered
            self._source_label_to_code = {
                label.casefold(): code for code, label in discovered.items() if label
            }
            self.logger.debug("Loaded %s AVR input source labels", len(discovered))
        else:
            self.logger.debug("Falling back to default input source labels")

    async def _async_fetch_source_map(self) -> dict[str, str]:
        async with self._lock:
            await self.connect()

            assert self._writer is not None
            assert self._reader is not None

            self._writer.write("SSFUN ?\r".encode("ascii"))
            await self._writer.drain()

            loop = asyncio.get_running_loop()
            deadline = loop.time() + 2.5
            discovered: dict[str, str] = {}

            while True:
                remaining = deadline - loop.time()
                if remaining <= 0:
                    break

                try:
                    response = await asyncio.wait_for(self._reader.readuntil(b"\r"), timeout=remaining)
                except TimeoutError:
                    break

                decoded = response.decode("ascii", errors="ignore").strip()
                upper = decoded.upper()

                if upper.startswith("E"):
                    return {}

                if not upper.startswith("SSFUN"):
                    continue

                payload = decoded[5:].strip()
                if not payload:
                    continue

                if payload.upper() == "END":
                    break

                code, label = self._parse_ssfun_payload(payload)
                if code and label:
                    discovered[code] = label

            return discovered

    @staticmethod
    def _parse_ssfun_payload(payload: str) -> tuple[str | None, str | None]:
        parts = payload.split()
        if not parts:
            return None, None

        code = parts[0].strip().upper()
        if len(parts) == 1:
            return code, parts[0].strip()

        label = " ".join(parts[1:]).strip()
        if not label:
            label = parts[0].strip()

        return code, label

    def _source_label_from_code(self, code: str | None) -> str | None:
        if not code:
            return None

        normalized = code.strip().upper()
        if normalized in self._source_code_to_label:
            return self._source_code_to_label[normalized]

        return code.strip()

    def _source_options(self, current_source: str | None) -> list[str]:
        options = list(DEFAULT_INPUT_SOURCES)
        options.extend(self._source_code_to_label.values())
        if current_source:
            options.append(current_source)

        deduped: list[str] = []
        seen: set[str] = set()
        for option in options:
            normalized = option.casefold()
            if normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(option)

        return deduped

    async def _async_query_optional(self, command: str) -> str | None:
        try:
            return await self._async_send(command)
        except Exception as err:
            self.logger.debug("Optional AVR status query failed for %s: %s", command, err)
            return None

    async def async_set_power(self, on: bool) -> None:
        await self._async_send("PWON" if on else "PWSTANDBY", allow_timeout=True)

    async def async_volume_up(self) -> None:
        await self._async_send("MVUP", allow_timeout=True)

    async def async_volume_down(self) -> None:
        await self._async_send("MVDOWN", allow_timeout=True)

    async def async_set_volume_level(self, level: float) -> None:
        avr_value = max(0, min(98, int(round(level * 98))))
        await self._async_send(f"MV{avr_value:02d}", allow_timeout=True)

    async def async_set_mute(self, mute: bool) -> None:
        await self._async_send("MUON" if mute else "MUOFF", allow_timeout=True)

    async def async_set_source(self, source: str) -> None:
        source_code = self._source_label_to_code.get(source.strip().casefold(), source)
        await self._async_send(f"SI{source_code}", allow_timeout=True)

    async def async_set_sound_mode(self, sound_mode: str) -> None:
        command_value = sound_mode.replace(" ", "")
        await self._async_send(f"MS{command_value}", allow_timeout=True)

    @staticmethod
    def _parse_volume(raw: str) -> float:
        value = raw.replace("MV", "")
        try:
            return max(0.0, min(1.0, int(value[:2]) / 98.0))
        except (TypeError, ValueError, IndexError):
            return 0.0

    @staticmethod
    def _parse_power(raw: str) -> str:
        value = raw.upper().replace("PW", "", 1).strip()
        if value.startswith("ON"):
            return "ON"
        return "OFF"

    @staticmethod
    def _strip_prefix(raw: str | None, prefix: str) -> str | None:
        if not raw:
            return None
        upper_prefix = prefix.upper()
        if raw.upper().startswith(upper_prefix):
            return raw[len(prefix) :].strip() or None
        return raw.strip() or None
