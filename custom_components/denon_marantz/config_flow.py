from __future__ import annotations

import logging
from urllib.parse import urlparse

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import dhcp
from homeassistant.components import ssdp
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_PORT, DEFAULT_NAME, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

UPNP_MANUFACTURER_KEYS = ("manufacturer", "upnp_manufacturer")
UPNP_MODEL_NAME_KEYS = ("modelName", "model_name", "upnp_model_name")
UPNP_DEVICE_TYPE_KEYS = ("deviceType", "device_type", "upnp_device_type")
UPNP_FRIENDLY_NAME_KEYS = ("friendlyName", "friendly_name", "upnp_friendly_name")


class DenonMarantzConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._discovered_host: str | None = None
        self._discovered_name: str | None = None

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_ssdp(self, discovery_info: ssdp.SsdpServiceInfo) -> FlowResult:
        st = self._get_ssdp_value(discovery_info, ssdp.ATTR_SSDP_ST, "ssdp_st")
        usn = self._get_ssdp_value(discovery_info, ssdp.ATTR_SSDP_USN, "ssdp_usn")
        location = self._get_ssdp_value(
            discovery_info,
            ssdp.ATTR_SSDP_LOCATION,
            "ssdp_location",
        )
        manufacturer = self._get_upnp_value(discovery_info, UPNP_MANUFACTURER_KEYS)
        model = self._get_upnp_value(discovery_info, UPNP_MODEL_NAME_KEYS)
        device_type = self._get_upnp_value(discovery_info, UPNP_DEVICE_TYPE_KEYS)
        friendly_name = self._get_upnp_value(discovery_info, UPNP_FRIENDLY_NAME_KEYS)

        _LOGGER.debug(
            "SSDP discovery candidate: st=%s usn=%s location=%s manufacturer=%s model=%s device_type=%s friendly_name=%s",
            st,
            usn,
            location,
            manufacturer,
            model,
            device_type,
            friendly_name,
        )

        if not location:
            _LOGGER.debug("SSDP discovery rejected: missing location")
            return self.async_abort(reason="cannot_connect")

        parsed = urlparse(location)
        host = parsed.hostname
        if not host:
            _LOGGER.debug("SSDP discovery rejected: unable to parse host from location=%s", location)
            return self.async_abort(reason="cannot_connect")

        self._async_abort_entries_match({CONF_HOST: host})

        await self.async_set_unique_id(host)
        self._abort_if_unique_id_configured()

        self._discovered_host = host
        self._discovered_name = friendly_name or f"{DEFAULT_NAME} ({host})"

        _LOGGER.debug(
            "SSDP discovery accepted: host=%s name=%s",
            self._discovered_host,
            self._discovered_name,
        )

        return await self.async_step_confirm()

    async def async_step_dhcp(self, discovery_info: dhcp.DhcpServiceInfo) -> FlowResult:
        host = str(getattr(discovery_info, "ip", "") or "")
        hostname = str(getattr(discovery_info, "hostname", "") or "")

        _LOGGER.debug(
            "DHCP discovery candidate: ip=%s hostname=%s",
            host,
            hostname,
        )

        if not host:
            _LOGGER.debug("DHCP discovery rejected: missing IP")
            return self.async_abort(reason="cannot_connect")

        self._async_abort_entries_match({CONF_HOST: host})

        await self.async_set_unique_id(host)
        self._abort_if_unique_id_configured()

        self._discovered_host = host
        self._discovered_name = hostname or f"{DEFAULT_NAME} ({host})"

        _LOGGER.debug(
            "DHCP discovery accepted: host=%s name=%s",
            self._discovered_host,
            self._discovered_name,
        )

        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            if not self._discovered_host:
                _LOGGER.debug("Discovery confirm failed: no discovered host in flow state")
                return self.async_abort(reason="cannot_connect")

            entry_data = {
                CONF_NAME: self._discovered_name or DEFAULT_NAME,
                CONF_HOST: self._discovered_host,
                CONF_PORT: DEFAULT_PORT,
            }
            return self.async_create_entry(title=entry_data[CONF_NAME], data=entry_data)

        self.context["title_placeholders"] = {
            "name": self._discovered_name or DEFAULT_NAME,
            "host": self._discovered_host or "",
        }
        return self.async_show_form(step_id="confirm")

    @staticmethod
    def _get_ssdp_value(
        discovery_info: ssdp.SsdpServiceInfo,
        key: str,
        attr_name: str,
    ) -> str | None:
        ssdp_data = getattr(discovery_info, "ssdp", None)
        if ssdp_data is not None and hasattr(ssdp_data, "get"):
            value = ssdp_data.get(key)
            if value:
                return str(value)

        ssdp_headers = getattr(discovery_info, "ssdp_headers", None)
        if ssdp_headers is not None and hasattr(ssdp_headers, "get"):
            value = ssdp_headers.get(key)
            if value:
                return str(value)

        value = getattr(discovery_info, attr_name, None)
        if value:
            return str(value)

        return None

    @staticmethod
    def _get_upnp_value(discovery_info: ssdp.SsdpServiceInfo, keys: tuple[str, ...]) -> str | None:
        upnp_data = getattr(discovery_info, "upnp", None)
        if upnp_data is not None and hasattr(upnp_data, "get"):
            for key in keys:
                value = upnp_data.get(key)
                if value:
                    return str(value)

        for key in keys:
            value = getattr(discovery_info, key, None)
            if value:
                return str(value)

        return None
