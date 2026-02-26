from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DEFAULT_NAME, DOMAIN


def build_device_info(entry: ConfigEntry) -> DeviceInfo:
    host = str(entry.data.get(CONF_HOST, "")).lower()
    name = entry.data.get(CONF_NAME) or DEFAULT_NAME

    return DeviceInfo(
        identifiers={(DOMAIN, host)},
        name=name,
        manufacturer="Denon / Marantz",
        model="AV Receiver",
    )
