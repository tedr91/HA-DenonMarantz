from __future__ import annotations

import logging
from urllib.parse import urlparse

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import ssdp
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_PORT, DEFAULT_NAME, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)


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
        _LOGGER.debug(
            "SSDP discovery candidate: st=%s usn=%s location=%s manufacturer=%s model=%s device_type=%s friendly_name=%s",
            discovery_info.ssdp.get(ssdp.ATTR_SSDP_ST),
            discovery_info.ssdp.get(ssdp.ATTR_SSDP_USN),
            discovery_info.ssdp.get(ssdp.ATTR_SSDP_LOCATION),
            discovery_info.upnp.get(ssdp.ATTR_UPNP_MANUFACTURER),
            discovery_info.upnp.get(ssdp.ATTR_UPNP_MODEL_NAME),
            discovery_info.upnp.get(ssdp.ATTR_UPNP_DEVICE_TYPE),
            discovery_info.upnp.get(ssdp.ATTR_UPNP_FRIENDLY_NAME),
        )

        location = discovery_info.upnp.get(ssdp.ATTR_SSDP_LOCATION)
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
        self._discovered_name = (
            discovery_info.upnp.get(ssdp.ATTR_UPNP_FRIENDLY_NAME)
            or f"{DEFAULT_NAME} ({host})"
        )

        _LOGGER.debug(
            "SSDP discovery accepted: host=%s name=%s",
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
