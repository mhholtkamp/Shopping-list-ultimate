"""Shopping List Ultimate integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

from .barcode import InvalidBarcode
from .const import (
    CONF_MERGE_DUPLICATES,
    CONF_TODO_ENTITY,
    DOMAIN,
    SERVICE_ADD_BARCODE,
    SERVICE_ADD_PRODUCT,
    SERVICE_DELETE_PRODUCT,
    SERVICE_LOOKUP_BARCODE,
    SERVICE_REFRESH_PRODUCT,
    SERVICE_UPDATE_PRODUCT,
)
from .coordinator import ShoppingCoordinator
from .openfoodfacts import OpenFoodFactsError
from .storage import ProductStore, display_name
from .todo import async_add_todo_item

PLATFORMS = ["sensor"]
BARCODE_SCHEMA = vol.Schema({vol.Required("barcode"): cv.string})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    store = ProductStore(hass)
    await store.async_load()
    coordinator = ShoppingCoordinator(hass, entry, store)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await _async_register_services(hass)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            for service in (SERVICE_LOOKUP_BARCODE, SERVICE_ADD_BARCODE, SERVICE_ADD_PRODUCT, SERVICE_UPDATE_PRODUCT, SERVICE_DELETE_PRODUCT, SERVICE_REFRESH_PRODUCT):
                hass.services.async_remove(DOMAIN, service)
    return unloaded


async def _async_reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


def _coordinator(hass: HomeAssistant) -> ShoppingCoordinator:
    try:
        return next(iter(hass.data[DOMAIN].values()))
    except (KeyError, StopIteration) as err:
        raise HomeAssistantError("Shopping List Ultimate is not configured") from err


async def _async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_LOOKUP_BARCODE):
        return

    async def lookup(call: ServiceCall) -> dict[str, Any]:
        try:
            product = await _coordinator(hass).async_lookup(call.data["barcode"])
            return {"found": product is not None, "product": product}
        except (InvalidBarcode, OpenFoodFactsError) as err:
            raise HomeAssistantError(str(err)) from err

    async def add_barcode(call: ServiceCall) -> dict[str, Any]:
        coordinator = _coordinator(hass)
        product = await coordinator.async_lookup(call.data["barcode"])
        if not product:
            raise HomeAssistantError("Product not found")
        options = {**coordinator.entry.data, **coordinator.entry.options}
        await async_add_todo_item(hass, call.data.get("todo_entity", options[CONF_TODO_ENTITY]), display_name(product), call.data.get("quantity", 1), call.data.get("note"), options[CONF_MERGE_DUPLICATES])
        return {"product": product}

    async def add_product(call: ServiceCall) -> dict[str, Any]:
        coordinator = _coordinator(hass)
        product = await coordinator.store.upsert({"barcode": call.data["barcode"], "name": call.data[CONF_NAME], "custom_name": None, "brand": call.data.get("brand", ""), "category": call.data.get("category", ""), "image": call.data.get("image", ""), "quantity": call.data.get("product_quantity", ""), "country": "", "source": "manual"})
        await coordinator.async_refresh()
        return {"product": product}

    async def update_product(call: ServiceCall) -> dict[str, Any]:
        coordinator = _coordinator(hass)
        try:
            product = await coordinator.store.update(call.data["barcode"], dict(call.data))
        except KeyError as err:
            raise HomeAssistantError("Product not found") from err
        await coordinator.async_refresh()
        return {"product": product}

    async def delete_product(call: ServiceCall) -> None:
        coordinator = _coordinator(hass)
        try:
            await coordinator.store.delete(call.data["barcode"])
        except KeyError as err:
            raise HomeAssistantError("Product not found") from err
        await coordinator.async_refresh()

    async def refresh_product(call: ServiceCall) -> dict[str, Any]:
        coordinator = _coordinator(hass)
        barcode = call.data["barcode"]
        product = await coordinator.client.lookup(barcode)
        if not product:
            raise HomeAssistantError("Product not found")
        current = coordinator.store.get(barcode) or {}
        product["custom_name"] = current.get("custom_name")
        product = await coordinator.store.upsert(product)
        await coordinator.async_refresh()
        return {"product": product}

    hass.services.async_register(DOMAIN, SERVICE_LOOKUP_BARCODE, lookup, schema=BARCODE_SCHEMA, supports_response=SupportsResponse.ONLY)
    hass.services.async_register(DOMAIN, SERVICE_ADD_BARCODE, add_barcode, schema=BARCODE_SCHEMA.extend({vol.Optional("todo_entity"): cv.entity_id, vol.Optional("quantity", default=1): vol.All(vol.Coerce(int), vol.Range(min=1)), vol.Optional("note"): cv.string}), supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, SERVICE_ADD_PRODUCT, add_product, schema=BARCODE_SCHEMA.extend({vol.Required(CONF_NAME): cv.string, vol.Optional("brand"): cv.string, vol.Optional("category"): cv.string, vol.Optional("image"): cv.url, vol.Optional("product_quantity"): cv.string}), supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, SERVICE_UPDATE_PRODUCT, update_product, schema=BARCODE_SCHEMA.extend({vol.Optional("custom_name"): cv.string, vol.Optional(CONF_NAME): cv.string, vol.Optional("brand"): cv.string, vol.Optional("category"): cv.string, vol.Optional("image"): cv.url, vol.Optional("quantity"): cv.string}), supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, SERVICE_DELETE_PRODUCT, delete_product, schema=BARCODE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_REFRESH_PRODUCT, refresh_product, schema=BARCODE_SCHEMA, supports_response=SupportsResponse.OPTIONAL)
