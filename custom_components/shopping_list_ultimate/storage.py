"""Persistent product storage backed by Home Assistant Store."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


class ProductStore:
    """Concurrency-safe local product repository."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._products: dict[str, dict[str, Any]] = {}

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self._products = data.get("products", {})

    async def _save(self) -> None:
        await self._store.async_save({"products": self._products})

    def get(self, barcode: str) -> dict[str, Any] | None:
        product = self._products.get(barcode)
        return deepcopy(product) if product else None

    def all(self) -> list[dict[str, Any]]:
        return sorted(
            (deepcopy(item) for item in self._products.values()),
            key=lambda item: item.get("last_scanned") or "",
            reverse=True,
        )

    async def upsert(self, product: dict[str, Any], *, scanned: bool = False) -> dict[str, Any]:
        barcode = str(product["barcode"])
        now = utcnow()
        current = self._products.get(barcode, {})
        merged = {**current, **{key: value for key, value in product.items() if value is not None}}
        merged.setdefault("created", now)
        merged.setdefault("scan_count", 0)
        if scanned:
            merged["scan_count"] += 1
            merged["last_scanned"] = now
        merged.setdefault("last_scanned", None)
        self._products[barcode] = merged
        await self._save()
        return deepcopy(merged)

    async def update(self, barcode: str, changes: dict[str, Any]) -> dict[str, Any]:
        if barcode not in self._products:
            raise KeyError(barcode)
        allowed = {"custom_name", "name", "brand", "category", "image", "quantity", "country"}
        return await self.upsert({"barcode": barcode, **{k: v for k, v in changes.items() if k in allowed}})

    async def delete(self, barcode: str) -> None:
        if self._products.pop(barcode, None) is None:
            raise KeyError(barcode)
        await self._save()


def display_name(product: dict[str, Any]) -> str:
    return product.get("custom_name") or product.get("name") or product["barcode"]
