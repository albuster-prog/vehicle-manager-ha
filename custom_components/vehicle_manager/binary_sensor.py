"""Binary sensor platform for Vehicle Manager HA — Warning alerts."""
from __future__ import annotations

import logging
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN, ALL_COUNTERS, COUNTERS_LEGAL,
    IDX_KEY, IDX_TYPES,
    STATUS_WARNING, STATUS_EXPIRED,
    CONF_VEHICLE_NAME, CONF_VEHICLE_TYPE, CONF_LICENSE_KEY,
    LICENSE_FREE, LICENSE_PRO,
)
from .license import get_license_tier
from .sensor import VehicleCounterSensor

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor warning entities for a vehicle."""
    data = entry.data
    vehicle_type = data.get(CONF_VEHICLE_TYPE, "ice")
    license_tier = get_license_tier(data.get(CONF_LICENSE_KEY))

    if license_tier == LICENSE_PRO:
        counters = [c for c in ALL_COUNTERS if vehicle_type in c[IDX_TYPES]]
    else:
        counters = [c for c in COUNTERS_LEGAL if vehicle_type in c[IDX_TYPES]]

    entities = [
        VehicleWarningBinarySensor(hass, entry, counter)
        for counter in counters
    ]
    async_add_entities(entities, update_before_add=True)


class VehicleWarningBinarySensor(BinarySensorEntity):
    """Binary sensor: ON when counter is WARNING or EXPIRED."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, counter: tuple) -> None:
        """Initialize."""
        self._hass = hass
        self._entry = entry
        self._counter = counter
        self._counter_key = counter[IDX_KEY]

        data = entry.data
        self._vehicle_name = data.get(CONF_VEHICLE_NAME, "Vehicle")
        self._vehicle_type = data.get(CONF_VEHICLE_TYPE, "ice")
        self._license_tier = get_license_tier(data.get(CONF_LICENSE_KEY))

        self._attr_unique_id = f"{entry.entry_id}_{self._counter_key}_warning"
        self._attr_name = f"{self._vehicle_name} {counter[1]} Warning"
        self._attr_icon = "mdi:alert-circle"

        # Reuse sensor logic
        self._sensor = VehicleCounterSensor(hass, entry, counter)

    @property
    def device_info(self) -> DeviceInfo:
        """Group under same device as sensors."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._vehicle_name,
            manufacturer="Vehicle Manager HA",
            model=self._vehicle_type.upper(),
        )

    @property
    def is_on(self) -> bool:
        """Return True if counter is warning or expired."""
        status = self._sensor._compute_status()
        return status in (STATUS_WARNING, STATUS_EXPIRED)

    @property
    def extra_state_attributes(self) -> dict:
        """Return status detail."""
        return {
            "status": self._sensor._compute_status(),
            "counter": self._counter_key,
        }

    async def async_update(self) -> None:
        """Update underlying sensor data."""
        await self._sensor.async_update()
