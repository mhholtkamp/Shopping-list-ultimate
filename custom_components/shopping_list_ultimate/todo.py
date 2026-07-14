"""Home Assistant todo list operations."""

from __future__ import annotations

from typing import Any

from homeassistant.components.todo import TodoItemStatus
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError


async def async_add_todo_item(
    hass: HomeAssistant,
    entity_id: str,
    name: str,
    quantity: int = 1,
    description: str | None = None,
    merge: bool = True,
) -> None:
    """Add an item, optionally merging an existing open item by its base name."""
    if not entity_id.startswith("todo.") or hass.states.get(entity_id) is None:
        raise HomeAssistantError(f"Todo entity {entity_id} is not available")
    target_name = name if quantity == 1 else f"{name} ×{quantity}"
    if merge:
        response: dict[str, Any] | None = await hass.services.async_call(
            "todo", "get_items", {ATTR_ENTITY_ID: entity_id}, blocking=True, return_response=True
        )
        items = (response or {}).get(entity_id, {}).get("items", [])
        for raw in items:
            summary = raw.get("summary", "")
            if raw.get("status") != TodoItemStatus.COMPLETED and (summary == name or summary.startswith(f"{name} ×")):
                old_quantity = int(summary.rsplit("×", 1)[1]) if " ×" in summary else 1
                await hass.services.async_call(
                    "todo",
                    "update_item",
                    {ATTR_ENTITY_ID: entity_id, "item": raw["uid"], "rename": f"{name} ×{old_quantity + quantity}"},
                    blocking=True,
                )
                return
    data: dict[str, Any] = {ATTR_ENTITY_ID: entity_id, "item": target_name}
    if description:
        data["description"] = description
    await hass.services.async_call("todo", "add_item", data, blocking=True)
