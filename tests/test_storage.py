from unittest.mock import AsyncMock, patch

import pytest

from custom_components.shopping_list_ultimate.storage import ProductStore, display_name


@pytest.mark.asyncio
async def test_store_lookup_update_delete():
    with patch("custom_components.shopping_list_ultimate.storage.Store") as cls:
        cls.return_value.async_load = AsyncMock(return_value=None)
        cls.return_value.async_save = AsyncMock()
        store = ProductStore(AsyncMock())
        await store.async_load()
        product = await store.upsert({"barcode": "4006381333931", "name": "Milk", "custom_name": None}, scanned=True)
        assert product["scan_count"] == 1
        await store.update(product["barcode"], {"custom_name": "Whole milk"})
        assert display_name(store.get(product["barcode"])) == "Whole milk"
        await store.delete(product["barcode"])
        assert store.get(product["barcode"]) is None
