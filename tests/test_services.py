from unittest.mock import MagicMock

import pytest

from custom_components.shopping_list_ultimate import _coordinator
from homeassistant.exceptions import HomeAssistantError


def test_coordinator_requires_configured_entry():
    hass = MagicMock()
    hass.data = {}
    with pytest.raises(HomeAssistantError):
        _coordinator(hass)
