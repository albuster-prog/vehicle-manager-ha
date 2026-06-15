"""Vehicle Manager HA — Custom Integration."""
from __future__ import annotations

import logging
from datetime import date
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import Platform
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DOMAIN,
    CONF_VEHICLE_NAME,
    CONF_NOTIFICATIONS_ENABLED,
    CONF_DISMISSED_NOTIFICATIONS,
    NOTIFICATIONS_ENABLED_DEFAULT,
    STATUS_WARNING, STATUS_EXPIRED,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Vehicle Manager from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    # Set up notification listener after platforms are loaded
    entry.async_on_unload(
        async_setup_notification_listener(hass, entry)
    )

    return True


def async_setup_notification_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Track binary sensor state changes and fire persistent notifications."""

    vehicle_name = entry.data.get(CONF_VEHICLE_NAME, "Vehicle")
    # Build list of binary sensor entity_ids for this entry
    # They follow the pattern: binary_sensor.<vehicle_name_slug>_<counter_key>_warning
    slug = vehicle_name.lower().replace(" ", "_").replace("-", "_")

    @callback
    def _on_binary_sensor_change(event):
        """Handle binary sensor state change."""
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        if new_state is None:
            return

        entity_id = new_state.entity_id
        notifications_enabled = entry.data.get(
            CONF_NOTIFICATIONS_ENABLED, NOTIFICATIONS_ENABLED_DEFAULT
        )
        if not notifications_enabled:
            return

        # Extract counter key from entity_id:
        # e.g. binary_sensor.kia_eniro_rca_warning -> strip prefix/suffix
        prefix = f"binary_sensor.{slug}_"
        suffix = "_warning"
        if not (entity_id.startswith(prefix) and entity_id.endswith(suffix)):
            return
        counter_key = entity_id[len(prefix):-len(suffix)]

        # Build a stable notification ID for this vehicle + counter + state
        sensor_status = new_state.attributes.get("status", "")
        notif_id = f"{DOMAIN}_{entry.entry_id}_{counter_key}_{sensor_status}"

        dismissed = list(entry.data.get(CONF_DISMISSED_NOTIFICATIONS, []))

        # Only notify when sensor turns ON (problem detected)
        if new_state.state != "on":
            # If it recovered to off, remove from dismissed so next warning fires again
            recovered_warning = f"{DOMAIN}_{entry.entry_id}_{counter_key}_{STATUS_WARNING}"
            recovered_expired = f"{DOMAIN}_{entry.entry_id}_{counter_key}_{STATUS_EXPIRED}"
            changed = False
            if recovered_warning in dismissed:
                dismissed.remove(recovered_warning)
                changed = True
            if recovered_expired in dismissed:
                dismissed.remove(recovered_expired)
                changed = True
            if changed:
                _save_dismissed(hass, entry, dismissed)
            return

        # Don't send if already dismissed by user
        if notif_id in dismissed:
            return

        # Don't re-send if it was already on (avoid spam on HA restarts)
        if old_state is not None and old_state.state == "on":
            old_status = old_state.attributes.get("status", "")
            if old_status == sensor_status:
                return

        # Build notification message
        friendly_name = new_state.name.replace(" Warning", "")
        days_remaining = new_state.attributes.get("days_remaining")

        if sensor_status == STATUS_EXPIRED:
            title = f"\u26a0\ufe0f {vehicle_name}: {friendly_name} EXPIRAT"
            if days_remaining is not None:
                message = (
                    f"{friendly_name} a expirat cu {abs(int(days_remaining))} zile in urma.\n"
                    f"Reinnoieste documentul cat mai curand posibil."
                )
            else:
                message = f"{friendly_name} a expirat. Reinnoieste documentul cat mai curand posibil."
        else:
            title = f"\U0001f514 {vehicle_name}: {friendly_name} expira curand"
            if days_remaining is not None:
                message = (
                    f"{friendly_name} expira in {int(days_remaining)} zile.\n"
                    f"Reinnoire necesara in curand."
                )
            else:
                message = f"{friendly_name} expira curand. Verifica data de expirare."

        hass.async_create_task(
            _async_send_notification(hass, entry, notif_id, title, message, dismissed)
        )

    async def _async_send_notification(hass, entry, notif_id, title, message, dismissed):
        """Create persistent notification and register dismiss listener."""
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "notification_id": notif_id,
                "title": title,
                "message": message,
            },
        )
        _LOGGER.info("Vehicle Manager: notification sent: %s", notif_id)

        # Listen for when the user dismisses this specific notification
        @callback
        def _on_notification_dismissed(event):
            dismissed_id = event.data.get("notification_id")
            if dismissed_id == notif_id:
                current_dismissed = list(entry.data.get(CONF_DISMISSED_NOTIFICATIONS, []))
                if notif_id not in current_dismissed:
                    current_dismissed.append(notif_id)
                    _save_dismissed(hass, entry, current_dismissed)
                    _LOGGER.debug("Vehicle Manager: notification dismissed and saved: %s", notif_id)

        hass.bus.async_listen_once(
            "persistent_notification.removed",
            _on_notification_dismissed,
        )

    # Track all binary sensors for this entry
    # Use a glob pattern to capture all warning sensors
    @callback
    def _async_track_sensors(_hass=hass, _entry=entry):
        """Register state tracking after entities are set up."""
        tracked_entities = [
            state.entity_id
            for state in hass.states.async_all("binary_sensor")
            if state.entity_id.startswith(f"binary_sensor.{slug}_")
            and state.entity_id.endswith("_warning")
        ]
        if tracked_entities:
            return async_track_state_change_event(
                hass, tracked_entities, _on_binary_sensor_change
            )
        return lambda: None

    # Delay tracking to after entities are registered
    async def _async_delayed_setup(_now=None):
        unsubscribe = _async_track_sensors()
        entry.async_on_unload(unsubscribe)

    # Schedule setup after current event loop tick
    hass.async_create_task(_async_delayed_setup())
    return lambda: None


def _save_dismissed(hass: HomeAssistant, entry: ConfigEntry, dismissed: list) -> None:
    """Persist the dismissed notification IDs into config entry data."""
    new_data = dict(entry.data)
    new_data[CONF_DISMISSED_NOTIFICATIONS] = dismissed
    hass.config_entries.async_update_entry(entry, data=new_data)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
