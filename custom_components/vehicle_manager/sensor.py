"""Sensor platform for Vehicle Manager HA."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN, ALL_COUNTERS, COUNTERS_LEGAL,
    IDX_KEY, IDX_LABEL_EN, IDX_LABEL_RO, IDX_DEFAULT_DAYS, IDX_DEFAULT_KM, IDX_TYPES,
    STATUS_OK, STATUS_WARNING, STATUS_EXPIRED, STATUS_UNKNOWN,
    ATTR_DAYS_REMAINING, ATTR_KM_REMAINING, ATTR_EXPIRY_DATE, ATTR_START_DATE,
    ATTR_LAST_DONE_DATE, ATTR_LAST_DONE_KM, ATTR_NEXT_DUE_DATE, ATTR_NEXT_DUE_KM,
    ATTR_PROGRESS_PCT, ATTR_LICENSE_TYPE, ATTR_VEHICLE_TYPE,
    CONF_VEHICLE_NAME, CONF_VEHICLE_TYPE, CONF_ODOMETER_ENTITY,
    CONF_LICENSE_KEY, CONF_WARNING_DAYS, WARNING_DAYS_DEFAULT,
    LICENSE_FREE, LICENSE_PRO,
)
from .license import get_license_tier

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities for a vehicle."""
    data = entry.data
    vehicle_type = data.get(CONF_VEHICLE_TYPE, "ice")
    license_tier = get_license_tier(data.get(CONF_LICENSE_KEY))

    # Determine which counters to create
    if license_tier == LICENSE_PRO:
        counters = [c for c in ALL_COUNTERS if vehicle_type in c[IDX_TYPES]]
    else:
        # Free: only legal documents
        counters = [c for c in COUNTERS_LEGAL if vehicle_type in c[IDX_TYPES]]

    entities = []
    for counter in counters:
        entities.append(
            VehicleCounterSensor(hass, entry, counter)
        )

    async_add_entities(entities, update_before_add=True)


class VehicleCounterSensor(SensorEntity):
    """Sensor representing a single maintenance counter or legal document."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, counter: tuple) -> None:
        """Initialize the sensor."""
        self._hass = hass
        self._entry = entry
        self._counter_key = counter[IDX_KEY]
        self._label_en = counter[IDX_LABEL_EN]
        self._label_ro = counter[IDX_LABEL_RO]
        self._default_days = counter[IDX_DEFAULT_DAYS]
        self._default_km = counter[IDX_DEFAULT_KM]

        data = entry.data
        self._vehicle_name = data.get(CONF_VEHICLE_NAME, "Vehicle")
        self._vehicle_type = data.get(CONF_VEHICLE_TYPE, "ice")
        self._odometer_entity = data.get(CONF_ODOMETER_ENTITY)
        self._warning_days = data.get(CONF_WARNING_DAYS, WARNING_DAYS_DEFAULT)
        self._license_tier = get_license_tier(data.get(CONF_LICENSE_KEY))

        # Unique ID: entry_id + counter key
        self._attr_unique_id = f"{entry.entry_id}_{self._counter_key}"
        self._attr_name = f"{self._vehicle_name} {self._label_en}"
        self._attr_icon = self._get_icon()

        self._counter_data: dict = data.get("counters", {}).get(self._counter_key, {})

    def _get_icon(self) -> str:
        """Return icon based on counter key."""
        icons = {
            "rca": "mdi:shield-car",
            "casco": "mdi:shield-check",
            "itp": "mdi:clipboard-check",
            "itp_ev": "mdi:clipboard-check",
            "rovinieta": "mdi:road",
            "tahograf": "mdi:gauge",
            "driving_license": "mdi:card-account-details",
            "oil_change": "mdi:oil",
            "air_filter": "mdi:air-filter",
            "fuel_filter": "mdi:fuel",
            "cabin_filter": "mdi:hvac",
            "spark_plugs": "mdi:lightning-bolt",
            "timing_belt": "mdi:cog-sync",
            "brake_fluid": "mdi:hydraulic-oil-level",
            "brake_pads_front": "mdi:car-brake-abs",
            "brake_pads_rear": "mdi:car-brake-abs",
            "brake_discs_front": "mdi:disc",
            "brake_discs_rear": "mdi:disc",
            "tyre_rotation": "mdi:tire",
            "tyre_balancing": "mdi:tire",
            "tyre_pressure": "mdi:gauge",
            "battery_12v": "mdi:battery-charging",
            "hv_battery_health": "mdi:battery-heart",
            "chain_lube": "mdi:link",
            "chain_replace": "mdi:link-variant",
            "moto_oil": "mdi:oil",
        }
        return icons.get(self._counter_key, "mdi:car-wrench")

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info to group sensors per vehicle."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._vehicle_name,
            manufacturer="Vehicle Manager HA",
            model=self._vehicle_type.upper(),
            sw_version=self._license_tier,
        )

    @property
    def native_value(self) -> str:
        """Return the status: ok / warning / expired / unknown."""
        return self._compute_status()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all computed attributes."""
        today = date.today()
        attrs: dict[str, Any] = {
            ATTR_VEHICLE_TYPE: self._vehicle_type,
            ATTR_LICENSE_TYPE: self._license_tier,
        }

        # Legal document style (start_date + expiry_date)
        if self._is_legal_counter():
            start_str = self._counter_data.get("start_date")
            expiry_str = self._counter_data.get("expiry_date")
            if start_str:
                attrs[ATTR_START_DATE] = start_str
            if expiry_str:
                attrs[ATTR_EXPIRY_DATE] = expiry_str
                try:
                    expiry = date.fromisoformat(expiry_str)
                    days_rem = (expiry - today).days
                    attrs[ATTR_DAYS_REMAINING] = days_rem
                    total = (expiry - date.fromisoformat(start_str)).days if start_str else 365
                    elapsed = (today - date.fromisoformat(start_str)).days if start_str else 0
                    attrs[ATTR_PROGRESS_PCT] = min(100, max(0, round(elapsed / max(total, 1) * 100)))
                except (ValueError, TypeError):
                    pass
        else:
            # Maintenance counter style (last_done_date + last_done_km)
            last_date_str = self._counter_data.get("last_done_date")
            last_km = self._counter_data.get("last_done_km")

            if last_date_str:
                attrs[ATTR_LAST_DONE_DATE] = last_date_str
                try:
                    last_date = date.fromisoformat(last_date_str)
                    if self._default_days:
                        due_date = last_date + timedelta(days=self._default_days)
                        attrs[ATTR_NEXT_DUE_DATE] = due_date.isoformat()
                        attrs[ATTR_DAYS_REMAINING] = (due_date - today).days
                        elapsed = (today - last_date).days
                        attrs[ATTR_PROGRESS_PCT] = min(100, max(0, round(elapsed / self._default_days * 100)))
                except (ValueError, TypeError):
                    pass

            if last_km is not None:
                attrs[ATTR_LAST_DONE_KM] = last_km
                current_km = self._get_current_odometer()
                if current_km and self._default_km:
                    next_km = last_km + self._default_km
                    attrs[ATTR_NEXT_DUE_KM] = next_km
                    attrs[ATTR_KM_REMAINING] = next_km - current_km

        return attrs

    def _is_legal_counter(self) -> bool:
        """Check if this is a legal document counter (has expiry_date style)."""
        legal_keys = {c[IDX_KEY] for c in COUNTERS_LEGAL}
        return self._counter_key in legal_keys

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

    def _compute_status(self) -> str:
        """Compute STATUS_OK / STATUS_WARNING / STATUS_EXPIRED / STATUS_UNKNOWN."""
        today = date.today()

        if self._is_legal_counter():
            start_str = self._counter_data.get("start_date")
            expiry_str = self._counter_data.get("expiry_date")
            if not expiry_str:
                return STATUS_UNKNOWN
            try:
                expiry = date.fromisoformat(expiry_str)
                # FIX: start_date in future is still VALID if expiry is in future
                if start_str:
                    start = date.fromisoformat(start_str)
                    if start > expiry:
                        return STATUS_UNKNOWN  # inverted dates — data error
                days_rem = (expiry - today).days
                if days_rem < 0:
                    return STATUS_EXPIRED
                if days_rem <= self._warning_days:
                    return STATUS_WARNING
                return STATUS_OK
            except (ValueError, TypeError):
                return STATUS_UNKNOWN
        else:
            last_date_str = self._counter_data.get("last_done_date")
            if not last_date_str:
                return STATUS_UNKNOWN
            try:
                last_date = date.fromisoformat(last_date_str)
                days_elapsed = (today - last_date).days
                if self._default_days and days_elapsed > self._default_days:
                    return STATUS_EXPIRED
                if self._default_days and days_elapsed > (self._default_days - self._warning_days):
                    return STATUS_WARNING
                # Check km
                current_km = self._get_current_odometer()
                last_km = self._counter_data.get("last_done_km")
                if current_km and last_km and self._default_km:
                    km_elapsed = current_km - last_km
                    if km_elapsed > self._default_km:
                        return STATUS_EXPIRED
                    if km_elapsed > (self._default_km - 2000):
                        return STATUS_WARNING
                return STATUS_OK
            except (ValueError, TypeError):
                return STATUS_UNKNOWN

    async def async_update(self) -> None:
        """Refresh counter data from config entry."""
        data = self._entry.data
        self._counter_data = data.get("counters", {}).get(self._counter_key, {})
        self._warning_days = data.get(CONF_WARNING_DAYS, WARNING_DAYS_DEFAULT)
