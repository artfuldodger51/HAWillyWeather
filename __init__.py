"""Willy Weather Forecaster integration for Home Assistant."""

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, SERVICE_SYNC_NOW
from .coordinator import WWForecasterCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["binary_sensor", "button", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Willy Weather Forecaster from a config entry."""
    coordinator = WWForecasterCoordinator(hass, entry)

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register options update listener
    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    # Register services
    async def handle_sync_now(call: ServiceCall) -> None:
        """Handle the sync_now service call."""
        entry_id = call.data.get("entry_id")

        if entry_id:
            # Sync specific entry
            if entry_id in hass.data[DOMAIN]:
                await hass.data[DOMAIN][entry_id].async_manual_sync()
            else:
                _LOGGER.error("Invalid entry_id: %s", entry_id)
        else:
            # Sync all entries
            for coordinator in hass.data[DOMAIN].values():
                await coordinator.async_manual_sync()

    hass.services.async_register(
        DOMAIN,
        SERVICE_SYNC_NOW,
        handle_sync_now,
        schema=cv.make_entity_service_schema({}),
    )

    _LOGGER.info("Willy Weather Forecaster integration set up successfully")
    return True
# hass.loop.create_task(coordinator.async_request_refresh())

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
