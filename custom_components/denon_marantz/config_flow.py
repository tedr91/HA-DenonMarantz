from __future__ import annotations

import logging
from urllib.parse import urlparse

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import dhcp, ssdp
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_ADD_EXTENDED_ENTITIES,
    CONF_INPUT_FILTER,
    CONF_PORT,
    DEFAULT_ADD_EXTENDED_ENTITIES,
    DEFAULT_INPUT_FILTER,
    DEFAULT_INPUT_SOURCES,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DOMAIN,
)
from .identity import async_probe_identity
from .migration import stable_id

_LOGGER = logging.getLogger(__name__)

UPNP_MANUFACTURER_KEYS = ("manufacturer", "upnp_manufacturer")
UPNP_MODEL_NAME_KEYS = ("modelName", "model_name", "upnp_model_name")
UPNP_DEVICE_TYPE_KEYS = ("deviceType", "device_type", "upnp_device_type")
UPNP_FRIENDLY_NAME_KEYS = ("friendlyName", "friendly_name", "upnp_friendly_name")


class DenonMarantzConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    def __init__(self) -> None:
        self._discovered_host: str | None = None
        self._discovered_name: str | None = None

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            host = user_input[CONF_HOST]
            try:
                identity = await async_probe_identity(host)
            except Exception:  # noqa: BLE001
                identity = None
            if identity is None:
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._user_schema(user_input),
                    errors={"base": "cannot_connect"},
                )
            await self.async_set_unique_id(identity.stable_id)
            self._abort_if_unique_id_configured(updates={CONF_HOST: host})
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(step_id="user", data_schema=self._user_schema())

    @staticmethod
    def _user_schema(defaults: dict | None = None) -> vol.Schema:
        defaults = defaults or {}
        host_field = (
            vol.Required(CONF_HOST, default=defaults[CONF_HOST])
            if CONF_HOST in defaults
            else vol.Required(CONF_HOST)
        )
        return vol.Schema(
            {
                vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
                host_field: str,
                vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): int,
            }
        )

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
        serial = self._get_upnp_value(discovery_info, ("serialNumber", "upnp_serial"))

        _LOGGER.debug(
            "SSDP discovery candidate: st=%s usn=%s location=%s manufacturer=%s "
            "model=%s device_type=%s friendly_name=%s",
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
            _LOGGER.debug(
                "SSDP discovery rejected: unable to parse host from location=%s", location
            )
            return self.async_abort(reason="cannot_connect")

        self._async_abort_entries_match({CONF_HOST: host})

        advertised_identity = stable_id(model, serial)
        await self.async_set_unique_id(advertised_identity or host)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})

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
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})

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
            try:
                identity = await async_probe_identity(self._discovered_host)
            except Exception:  # noqa: BLE001
                identity = None
            if identity is None:
                return self.async_abort(reason="cannot_connect")
            await self.async_set_unique_id(identity.stable_id, raise_on_progress=False)
            self._abort_if_unique_id_configured(updates={CONF_HOST: self._discovered_host})
            return self.async_create_entry(title=entry_data[CONF_NAME], data=entry_data)

        self.context["title_placeholders"] = {
            "name": self._discovered_name or DEFAULT_NAME,
            "host": self._discovered_host or "",
        }

        return self.async_show_form(
            step_id="confirm",
            description_placeholders={
                "name": self._discovered_name or DEFAULT_NAME,
                "host": self._discovered_host or "",
            },
        )

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

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> DenonMarantzOptionsFlow:
        return DenonMarantzOptionsFlow(config_entry)


class DenonMarantzOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_filter = self._normalize_filter(
            self._config_entry.options.get(CONF_INPUT_FILTER, DEFAULT_INPUT_FILTER)
        )

        filter_options = self._available_source_labels()
        for value in current_filter:
            if value not in filter_options:
                filter_options.append(value)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_INPUT_FILTER,
                    default=current_filter,
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=filter_options,
                        multiple=True,
                        custom_value=True,
                        mode=SelectSelectorMode.DROPDOWN,
                        sort=True,
                    )
                ),
                vol.Required(
                    CONF_ADD_EXTENDED_ENTITIES,
                    default=self._config_entry.options.get(
                        CONF_ADD_EXTENDED_ENTITIES,
                        DEFAULT_ADD_EXTENDED_ENTITIES,
                    ),
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

    @staticmethod
    def _normalize_filter(value: object) -> list[str]:
        if isinstance(value, list):
            return [str(token).strip() for token in value if str(token).strip()]
        return []

    def _available_source_labels(self) -> list[str]:
        runtime = getattr(self._config_entry, "runtime_data", None)
        client = runtime.client if runtime is not None else None
        if client is not None:
            try:
                return client.available_source_labels()
            except Exception:  # noqa: BLE001 - fall back to defaults on any failure
                pass
        return list(DEFAULT_INPUT_SOURCES)
