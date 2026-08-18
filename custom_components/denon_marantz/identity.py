from __future__ import annotations

from dataclasses import dataclass

from denonavr import DenonAVR

from .migration import stable_id


@dataclass(frozen=True)
class DenonMarantzIdentity:
    """Authenticated receiver identity."""

    stable_id: str
    name: str
    manufacturer: str
    model: str
    serial: str


async def async_probe_identity(host: str) -> DenonMarantzIdentity | None:
    """Read stable receiver identity over the Denon HTTP API."""
    receiver = DenonAVR(host=host, timeout=5.0)
    await receiver.async_setup()
    identity = stable_id(receiver.model_name, receiver.serial_number)
    if identity is None:
        return None
    return DenonMarantzIdentity(
        stable_id=identity,
        name=receiver.name or "",
        manufacturer=receiver.manufacturer or "Denon / Marantz",
        model=receiver.model_name or "AV Receiver",
        serial=receiver.serial_number or "",
    )
