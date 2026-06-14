"""Config flow for Vehicle Manager HA."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    VEHICLE_TYPES,
    CONF_VEHICLE_NAME, CONF_VEHICLE_TYPE, CONF_LICENSE_PLATE,
    CONF_VIN, CONF_ODOMETER_ENTITY, CONF_UNIT, CONF_LICENSE_KEY, CONF_WARNING_DAYS,
    UNIT_KM, UNIT_MILES, WARNING_DAYS_DEFAULT,
    FREE_MAX_VEHICLES,
)
from .license import get_license_tier, validate_license_format


class VehicleManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the Vehicle Manager config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._data: dict = {}

    async def async_step_user(self, user_input=None):
        """Step 1: Basic vehicle info."""
        errors = {}

        # Check free tier vehicle limit
        existing = self._async_current_entries()
        license_key = None
        if existing:
            # Use the license from the first entry (shared)
            license_key = existing[0].data.get(CONF_LICENSE_KEY)
        tier = get_license_tier(license_key)

        if tier == "free" and len(existing) >= FREE_MAX_VEHICLES:
            return self.async_abort(reason="free_tier_limit")

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_license()

        schema = vol.Schema({
            vol.Required(CONF_VEHICLE_NAME): str,
            vol.Required(CONF_VEHICLE_TYPE, default="ice"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"value": "ice",      "label": "Car — Gasoline/Diesel (ICE)"},
                        {"value": "ev",       "label": "Car — Electric (EV)"},
                        {"value": "hev",      "label": "Car — Hybrid (HEV)"},
                        {"value": "phev",     "label": "Car — Plug-in Hybrid (PHEV)"},
                        {"value": "moto_ice", "label": "Motorcycle — ICE"},
                        {"value": "moto_ev",  "label": "Motorcycle — Electric"},
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_LICENSE_PLATE): str,
            vol.Optional(CONF_VIN): str,
            vol.Optional(CONF_ODOMETER_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Optional(CONF_UNIT, default=UNIT_KM): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"value": UNIT_KM,    "label": "Kilometers (km)"},
                        {"value": UNIT_MILES, "label": "Miles (mi)"},
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_WARNING_DAYS, default=WARNING_DAYS_DEFAULT): int,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_license(self, user_input=None):
        """Step 2: License key (optional, skip for Free)."""
        errors = {}

        if user_input is not None:
            key = user_input.get(CONF_LICENSE_KEY, "").strip()
            if key and not validate_license_format(key):
                errors[CONF_LICENSE_KEY] = "invalid_license_format"
            else:
                self._data[CONF_LICENSE_KEY] = key if key else None
                self._data["counters"] = {}
                return self.async_create_entry(
                    title=self._data[CONF_VEHICLE_NAME],
                    data=self._data,
                )

        schema = vol.Schema({
            vol.Optional(CONF_LICENSE_KEY, description={"suggested_value": ""}): str,
        })

        return self.async_show_form(
            step_id="license",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "bmac_url": "https://www.buymeacoffee.com/vehiclemanagerha",
                "format": "VM-XXXX-XXXX-XXXX-XXXX",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return options flow handler."""
        return VehicleManagerOptionsFlow(config_entry)


class VehicleManagerOptionsFlow(config_entries.OptionsFlow):
    """Handle options (update counter data)."""

    def __init__(self, config_entry) -> None:
        """Initialize."""
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        """Show options menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["update_counter", "update_legal", "update_license"],
        )

    async def async_step_update_license(self, user_input=None):
        """Update license key."""
        errors = {}
        if user_input is not None:
            key = user_input.get(CONF_LICENSE_KEY, "").strip()
            if key and not validate_license_format(key):
                errors[CONF_LICENSE_KEY] = "invalid_license_format"
            else:
                new_data = dict(self._entry.data)
                new_data[CONF_LICENSE_KEY] = key if key else None
                self.hass.config_entries.async_update_entry(self._entry, data=new_data)
                return self.async_create_entry(title="", data={})

        schema = vol.Schema({
            vol.Optional(
                CONF_LICENSE_KEY,
                description={"suggested_value": self._entry.data.get(CONF_LICENSE_KEY, "")},
            ): str,
        })
        return self.async_show_form(
            step_id="update_license", data_schema=schema, errors=errors
        )

    async def async_step_update_legal(self, user_input=None):
        """Update legal document dates (RCA, CASCO, ITP, Rovinieta)."""
        errors = {}
        if user_input is not None:
            new_data = dict(self._entry.data)
            counters = dict(new_data.get("counters", {}))
            doc_key = user_input.pop("doc_key", None)
            if doc_key:
                counters[doc_key] = {
                    "start_date": user_input.get("start_date"),
                    "expiry_date": user_input.get("expiry_date"),
                }
                new_data["counters"] = counters
                self.hass.config_entries.async_update_entry(self._entry, data=new_data)
            return self.async_create_entry(title="", data={})

        schema = vol.Schema({
            vol.Required("doc_key"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"value": "rca",       "label": "RCA Insurance"},
                        {"value": "casco",     "label": "CASCO Insurance"},
                        {"value": "itp",       "label": "Vehicle Inspection (ITP)"},
                        {"value": "itp_ev",    "label": "Vehicle Inspection EV (ITP)"},
                        {"value": "rovinieta", "label": "Road Vignette (Rovinieta)"},
                        {"value": "tahograf",  "label": "Tachograph"},
                        {"value": "driving_license", "label": "Driving License"},
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional("start_date"): selector.DateSelector(),
            vol.Optional("expiry_date"): selector.DateSelector(),
        })
        return self.async_show_form(
            step_id="update_legal", data_schema=schema, errors=errors
        )

    async def async_step_update_counter(self, user_input=None):
        """Update a maintenance counter (last done date + km)."""
        errors = {}
        if user_input is not None:
            new_data = dict(self._entry.data)
            counters = dict(new_data.get("counters", {}))
            counter_key = user_input.pop("counter_key", None)
            if counter_key:
                counters[counter_key] = {
                    "last_done_date": user_input.get("last_done_date"),
                    "last_done_km": user_input.get("last_done_km"),
                }
                new_data["counters"] = counters
                self.hass.config_entries.async_update_entry(self._entry, data=new_data)
            return self.async_create_entry(title="", data={})

        schema = vol.Schema({
            vol.Required("counter_key"): str,
            vol.Optional("last_done_date"): selector.DateSelector(),
            vol.Optional("last_done_km"): int,
        })
        return self.async_show_form(
            step_id="update_counter", data_schema=schema, errors=errors
        )
