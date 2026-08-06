"""The Electrolux Control integration."""
import base64
import json
import logging

import broadlink

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady

from homeassistant.const import CONF_HOST, CONF_TIMEOUT, CONF_NAME, CONF_MAC
from homeassistant.components.climate.const import ATTR_MAX_TEMP, ATTR_MIN_TEMP

from broadlink import DEFAULT_TIMEOUT
from broadlink.exceptions import BroadlinkException

from .const import PLATFORMS, DEFAULT_MIN, DEFAULT_MAX, DOMAIN
from .electrolux import create_from_device, DEVICE_TYPE

_LOGGER = logging.getLogger(__name__)


def _discover_serial(host: str) -> str:
    """Discover the device at `host` and read its serial number.

    This does a UDP broadcast discovery plus a status round-trip - both
    blocking network calls. Only ever call this via an executor job, never
    directly from the event loop.
    """
    discovery = broadlink.discover(discover_ip_address=host)

    if not discovery or discovery[0].devtype != DEVICE_TYPE:
        return ""

    status = json.loads(create_from_device(discovery[0]).get_status())
    return status.get("sn", "")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Electrolux Control from a config entry."""

    host = entry.data[CONF_HOST]
    mac = bytes.fromhex(entry.data[CONF_MAC])

    # Discovery + status fetch happens once here, off the event loop, and the
    # result is shared with both platforms below - previously climate.py and
    # switch.py each repeated this (blocking) work independently.
    try:
        sn = await hass.async_add_executor_job(_discover_serial, host)
    except (BroadlinkException, OSError) as err:
        # Device is temporarily unreachable (e.g. mid-reconnect, or just
        # rebooting) - ask HA to retry setup later rather than failing for good.
        raise ConfigEntryNotReady(f"Could not reach {host}: {err}") from err

    if not sn:
        _LOGGER.warning(
            "Electrolux device at %s did not report a serial number; "
            "falling back to its MAC address as a unique id",
            host,
        )
        sn = mac.hex()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"sn": sn}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unloaded


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate an old config entry to the current version."""
    if config_entry.version == 1:
        new_data = {**config_entry.data}
        new_title = config_entry.title

        if "ip" in config_entry.data:
            new_title = "ELECTROLUX_OEM"
            new_data[CONF_NAME] = config_entry.title
            new_data[CONF_HOST] = config_entry.data["ip"]
            new_data[CONF_MAC] = base64.b64decode(config_entry.data["mac"]).hex()
            new_data[CONF_TIMEOUT] = DEFAULT_TIMEOUT
            new_data[ATTR_MIN_TEMP] = DEFAULT_MIN
            new_data[ATTR_MAX_TEMP] = DEFAULT_MAX

        # Version and title/data must go through async_update_entry - setting
        # config_entry.version directly isn't guaranteed to stick on current
        # HA core.
        hass.config_entries.async_update_entry(
            config_entry, title=new_title, data=new_data, version=2
        )

    return True
