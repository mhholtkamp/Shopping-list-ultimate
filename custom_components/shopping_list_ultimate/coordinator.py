"""Runtime coordinator for product lookup and scan state."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .barcode import validate_barcode
from .const import CONF_COUNTRY, CONF_LANGUAGE, DOMAIN, EVENT_BARCODE_SCANNED
from .openfoodfacts import OpenFoodFactsClient
from .storage import ProductStore


class ShoppingCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, store: ProductStore) -> None:
        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            name=DOMAIN,
            config_entry=entry,
        )
        self.entry = entry
        config = {**entry.data, **entry.options}
        self.store = store
        self.client = OpenFoodFactsClient(async_get_clientsession(hass), config[CONF_COUNTRY], config[CONF_LANGUAGE])
        self.last_scanned: dict[str, Any] | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        products = self.store.all()
        return {"products": products, "known_products": len(products), "total_scans": sum(p["scan_count"] for p in products)}

    async def async_lookup(self, raw_barcode: str, *, record_scan: bool = True) -> dict[str, Any] | None:
        barcode = validate_barcode(raw_barcode).value
        product = self.store.get(barcode)
        source = "local" if product else "open_food_facts"
        if not product:
            product = await self.client.lookup(barcode)
        if product and record_scan:
            product = await self.store.upsert(product, scanned=True)
        self.last_scanned = product or {"barcode": barcode, "source": source}
        self.hass.bus.async_fire(EVENT_BARCODE_SCANNED, {
            "barcode": barcode, "found": product is not None,
            "product_name": (product or {}).get("custom_name") or (product or {}).get("name"), "source": source,
        })
        await self.async_refresh()
        return product
