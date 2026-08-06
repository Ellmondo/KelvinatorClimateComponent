import json
import logging
import typing as t

import broadlink

from .electrolux import electrolux, DEVICE_TYPE

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError

from .const import DOMAIN

from broadlink.const import DEFAULT_TIMEOUT
from broadlink.exceptions import AuthenticationError, NetworkTimeoutError, BroadlinkException

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add_entities_async) -> bool:
    """Set up Electrolux Control from a config entry."""

    host = entry.data[CONF_HOST]
    mac = bytes.fromhex(entry.data[CONF_MAC])
    name = entry.title

    # Shared with climate.py - discovered once in __init__.py's
    # async_setup_entry, not re-discovered per platform.
    sn = hass.data[DOMAIN][entry.entry_id]["sn"]

    ledDev = ElectroluxClimateLedEntity(hass, entry, sn, name, entry.data[CONF_NAME], (host, broadlink.DEFAULT_PORT), mac)
    if not await ledDev.async_setup():
        return False

    add_entities_async([ledDev], True)

    return True


class ElectroluxClimateLedEntity(SwitchEntity):

    def __init__(self,
        hass: HomeAssistant,
        config: ConfigEntry,
        sn: str,
        name: str,
        dev_name: str,
        host: t.Tuple[str, int],
        mac: t.Union[bytes, str]):
        super().__init__()
        self.hass = hass
        self.config = config

        self.host = host
        self.mac = mac

        self.sn = sn
        self._attr_unique_id = sn + "-led"
        self._attr_name = name + " LED"
        self.dev_name = dev_name + " LED"

    def update(self):
        try:
            state = json.loads(self.device.get_status())
        except (NetworkTimeoutError, OSError, BroadlinkException) as err:
            # Same brief, expected reconnect window as the climate entity -
            # mark unavailable quietly instead of raising every 5 seconds.
            _LOGGER.debug("Electrolux %s unreachable during poll: %s", self.dev_name, err)
            self._attr_available = False
            return

        # Previously this read state["sn"] directly, which threw a KeyError
        # if a status response ever came back without "sn" - climate.py
        # already guarded this; switch.py did not.
        if "sn" in state and state["sn"] != self.sn:
            self._attr_available = False
            return

        self._attr_available = True
        self._attr_is_on = state['scrdisp'] == 1

    def _run(self, action, *args):
        """Run a device command, turning a transient network error into a
        clean HomeAssistantError instead of a raw traceback in the UI."""
        try:
            return action(*args)
        except (NetworkTimeoutError, OSError, BroadlinkException) as err:
            raise HomeAssistantError(
                f"Couldn't reach {self.dev_name}: {err}"
            ) from err

    def turn_on(self):
        self._run(self.device.set_led, True)

    def turn_off(self):
        self._run(self.device.set_led, False)

    async def async_setup(self):
        """Set up the device and related entities."""

        self.device = electrolux(
            self.host,
            self.mac,
            DEVICE_TYPE,
            DEFAULT_TIMEOUT,
            self.dev_name,
            "",
            "Electrolux",
            False)

        try:
            await self.hass.async_add_executor_job(
                self.device.auth
            )

        except AuthenticationError:
            return False

        except (NetworkTimeoutError, OSError) as err:
            raise ConfigEntryNotReady from err

        except BroadlinkException:
            return False

        return True

    @property
    def device_info(self) -> dr.DeviceInfo:
        """Return device info."""
        return dr.DeviceInfo(
            connections={(dr.CONNECTION_NETWORK_MAC, self.mac.hex())},
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=self.name
        )
