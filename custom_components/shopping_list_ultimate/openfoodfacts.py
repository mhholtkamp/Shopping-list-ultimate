"""Async Open Food Facts API client."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientSession

USER_AGENT = "Shopping List Ultimate for Home Assistant/0.1"


class OpenFoodFactsError(Exception):
    """Open Food Facts request failed."""


def parse_product(payload: dict[str, Any], barcode: str) -> dict[str, Any] | None:
    """Convert an API v2 response into the local product model."""
    if payload.get("status") != 1 or not (data := payload.get("product")):
        return None
    countries = data.get("countries_tags") or []
    categories = data.get("categories_tags") or []
    return {
        "barcode": barcode,
        "name": data.get("product_name") or data.get("generic_name") or "",
        "custom_name": None,
        "brand": data.get("brands") or "",
        "category": (categories[0].removeprefix("en:") if categories else ""),
        "image": data.get("image_front_url") or data.get("image_url") or "",
        "quantity": data.get("quantity") or "",
        "country": (countries[0].split(":", 1)[-1] if countries else ""),
        "source": "open_food_facts",
    }


class OpenFoodFactsClient:
    """Small API v2 client using Home Assistant's shared session."""

    def __init__(self, session: ClientSession, country: str, language: str) -> None:
        self._session = session
        self._country = country
        self._language = language

    async def lookup(self, barcode: str) -> dict[str, Any] | None:
        url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
        params = {
            "fields": (
                "code,product_name,generic_name,brands,categories_tags,"
                "image_front_url,image_url,quantity,countries_tags"
            )
        }
        headers = {"User-Agent": USER_AGENT, "Accept-Language": self._language}
        try:
            async with self._session.get(url, params=params, headers=headers, timeout=15) as response:
                if response.status == 404:
                    return None
                response.raise_for_status()
                return parse_product(await response.json(), barcode)
        except (ClientError, TimeoutError, ValueError) as err:
            raise OpenFoodFactsError("Open Food Facts is unavailable") from err
