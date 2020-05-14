""" Config Flow to configure Unifi Protect Integration. """
import logging

from pyunifiprotect import UpvServer, NotAuthorized, NvrError

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_PORT,
)

from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_ID
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from aiohttp import CookieJar

from .const import (
    DOMAIN,
    DEFAULT_PORT,
)

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class UnifiProtectFlowHandler(ConfigFlow):
    """Handle a Unifi Protect config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def _show_setup_form(self, errors=None):
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Required(CONF_USERNAME): str,
                    vol.Optional(CONF_PASSWORD): str,
                }
            ),
            errors=errors or {},
        )

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        if user_input is None:
            return await self._show_setup_form(user_input)

        errors = {}

        session = async_create_clientsession(
            self.hass, cookie_jar=CookieJar(unsafe=True)
        )

        unifiprotect = UpvServer(
            session,
            user_input[CONF_HOST],
            user_input[CONF_PORT],
            user_input[CONF_USERNAME],
            user_input[CONF_PASSWORD],
        )

        try:
            unique_id = await unifiprotect.unique_id()
        except NotAuthorized:
            errors["base"] = "connection_error"
            return await self._show_setup_form(errors)
        except NvrError:
            errors["base"] = "nvr_error"
            return await self._show_setup_form(errors)

        entries = self._async_current_entries()
        for entry in entries:
            if entry.data[CONF_ID] == unique_id:
                return self.async_abort(reason="server_exists")

        return self.async_create_entry(
            title=unique_id,
            data={
                CONF_ID: unique_id,
                CONF_HOST: user_input[CONF_HOST],
                CONF_PORT: user_input[CONF_PORT],
                CONF_USERNAME: user_input.get(CONF_USERNAME),
                CONF_PASSWORD: user_input.get(CONF_PASSWORD),
            },
        )
