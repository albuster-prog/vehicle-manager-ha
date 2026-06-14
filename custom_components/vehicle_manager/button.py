"""Button platform for Vehicle Manager HA — Mark as Done today."""
from __future__ import annotations

import logging
from datetime import date

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN, ALL_COUNTERS, COUNTERS_LEGAL,
    IDX_KEY, IDX_LABEL_EN, IDX_TYPES,
    CONF_VEHICLE_NAME, CONF_VEHICLE_TYPE, CONF_LICENSE_KEY, CONF_ODOMETER_ENTITY,
    LICENSE_PRO,
)
from .license import get_license_tier

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Done buttons for each maintenance counter."""
    data = entry.data
    vehicle_type = data.get(CONF_VEHICLE_TYPE, "ice")
    license_tier = get_license_tier(data.get(CONF_LICENSE_KEY))

    # Legal counters don't get a "done" button (they have explicit dates)
    legal_keys = {c[IDX_KEY] for c in COUNTERS_LEGAL}

    if license_tier == LICENSE_PRO:
        counters = [
            c for c in ALL_COUNTERS
            if vehicle_type in c[IDX_TYPES] and c[IDX_KEY] not in legal_keys
        ]
    else:
        counters = []  # No Done buttons in Free tier (no maintenance counters)

    entities = [MarkDoneButton(hass, entry, counter) for counter in counters]
    async_add_entities(entities)


class MarkDoneButton(ButtonEntity):
    """Button to mark a maintenance item as done today at current odometer."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, counter: tuple) -> None:
        """Initialize."""
        self._hass = hass
        self._entry = entry
        self._counter_key = counter[IDX_KEY]
        self._label_en = counter[IDX_LABEL_EN]

        data = entry.data
        self._vehicle_name = data.get(CONF_VEHICLE_NAME, "Vehicle")
        self._vehicle_type = data.get(CONF_VEHICLE_TYPE, "ice")
        self._odometer_entity = data.get(CONF_ODOMETER_ENTITY)

        self._attr_unique_id = f"{entry.entry_id}_{self._counter_key}_done"
        self._attr_name = f"{self._vehicle_name} {self._label_en} — Done"
        self._attr_icon = "mdi:check-circle"

    @property
    def device_info(self) -> DeviceInfo:
        """Group under same device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._vehicle_name,
            manufacturer="Vehicle Manager HA",
            model=self._vehicle_type.upper(),
        )

    async def async_press(self) -> None:
        """Handle button press: save today + current km to config entry."""
        today = date.today().isoformat()
        current_km = self._get_current_odometer()

        # Update the config entry data with the new "last done" info
        data = dict(self._entry.data)
        counters = dict(data.get("counters", {}))
        counter_data = dict(counters.get(self._counter_key, {}))

        counter_data["last_done_date"] = today
        if current_km is not None:
            counter_data["last_done_km"] = current_km

        counters[self._counter_key] = counter_data
        data["counters"] = counters

        self._hass.config_entries.async_update_entry(self._entry, data=data)
        _LOGGER.info(
            "Marked %s as done for %s (date=%s, km=%s)",
            self._counter_key, self._vehicle_name, today, current_km
        )

    def _get_current_odometer(self) -> int | None:
        """Get current odometer reading from HA entity."""
        if not self._odometer_entity:
            return None
        state = self._hass.states.get(self._odometer_entity)
        if state and state.state not in ("unknown", "unavailable"):
            try:
                return int(float(state.state))
            except (ValueError, TypeError):
                pass
        return None
