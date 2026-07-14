from unittest.mock import MagicMock

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.shopping_list_ultimate import _coordinator


def test_coordinator_requires_configured_entry():
    hass = MagicMock()
    hass.data = {}
    with pytest.raises(HomeAssistantError):
        _coordinator(hass)
