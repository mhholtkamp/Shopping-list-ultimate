from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.shopping_list_ultimate.todo import async_add_todo_item


@pytest.mark.asyncio
async def test_add_todo_item():
    hass = MagicMock()
    hass.states.get.return_value = MagicMock()
    hass.services.async_call = AsyncMock(return_value={"todo.shopping": {"items": []}})
    await async_add_todo_item(hass, "todo.shopping", "Milk", 2)
    assert hass.services.async_call.await_args_list[-1].args[1] == "add_item"
    assert hass.services.async_call.await_args_list[-1].args[2]["item"] == "Milk ×2"
