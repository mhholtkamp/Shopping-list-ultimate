"""UI configuration flow."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_AUTO_ADD,
    CONF_COUNTRY,
    CONF_LANGUAGE,
    CONF_MERGE_DUPLICATES,
    CONF_STORE_UNKNOWN,
    CONF_TODO_ENTITY,
    CONF_USE_IMAGES,
    DEFAULT_COUNTRY,
    DEFAULT_LANGUAGE,
    DOMAIN,
)


def schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema({
        vol.Required(CONF_TODO_ENTITY, default=defaults.get(CONF_TODO_ENTITY)): selector.EntitySelector(selector.EntitySelectorConfig(domain="todo")),
        vol.Required(CONF_COUNTRY, default=defaults.get(CONF_COUNTRY, DEFAULT_COUNTRY)): str,
        vol.Required(CONF_LANGUAGE, default=defaults.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)): selector.LanguageSelector(),
        vol.Required(CONF_USE_IMAGES, default=defaults.get(CONF_USE_IMAGES, True)): bool,
        vol.Required(CONF_AUTO_ADD, default=defaults.get(CONF_AUTO_ADD, False)): bool,
        vol.Required(CONF_STORE_UNKNOWN, default=defaults.get(CONF_STORE_UNKNOWN, True)): bool,
        vol.Required(CONF_MERGE_DUPLICATES, default=defaults.get(CONF_MERGE_DUPLICATES, True)): bool,
    })


class ShoppingListUltimateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Shopping List Ultimate", data=user_input)
        return self.async_show_form(step_id="user", data_schema=schema({}))
    @staticmethod
    def async_get_options_flow(config_entry):
        return OptionsFlow(config_entry)


class OptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry):
        self.entry = entry
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="init", data_schema=schema({**self.entry.data, **self.entry.options}))
