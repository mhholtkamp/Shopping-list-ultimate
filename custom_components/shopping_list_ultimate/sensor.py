"""Shopping List Ultimate sensors."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import ShoppingCoordinator
from .storage import display_name


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data["shopping_list_ultimate"][entry.entry_id]
    async_add_entities(
        [
            LastScannedSensor(coordinator, entry),
            CountSensor(coordinator, entry, "known_products", "Shopping List Ultimate known products", "mdi:barcode"),
            CountSensor(coordinator, entry, "total_scans", "Shopping List Ultimate total scans", "mdi:barcode-scan"),
        ]
    )


class BaseSensor(CoordinatorEntity[ShoppingCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key, name, icon):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{key}"


class CountSensor(BaseSensor):
    @property
    def native_value(self):
        return self.coordinator.data[self._key]

    @property
    def extra_state_attributes(self):
        if self._key != "known_products":
            return None
        return {"recent_products": self.coordinator.data["products"][:10]}


class LastScannedSensor(BaseSensor):
    def __init__(self, coordinator, entry):
        super().__init__(
            coordinator,
            entry,
            "last_scanned_product",
            "Shopping List Ultimate last scanned product",
            "mdi:barcode-scan",
        )

    @property
    def native_value(self):
        return display_name(self.coordinator.last_scanned) if self.coordinator.last_scanned else None

    @property
    def extra_state_attributes(self):
        product = self.coordinator.last_scanned
        if not product:
            return {"found": False}
        return {
            "barcode": product.get("barcode"),
            "name": display_name(product),
            "brand": product.get("brand"),
            "image": product.get("image"),
            "found": bool(product.get("name")),
            "source": product.get("source"),
        }
