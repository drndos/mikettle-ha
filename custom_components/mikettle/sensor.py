"""Support for Xiaomi Mi Kettle BLE."""
from datetime import timedelta
import logging

from mikettle.mikettle import MiKettle
from mikettle.mikettle import (
    MI_ACTION,
    MI_MODE,
    MI_SET_TEMPERATURE,
    MI_CURRENT_TEMPERATURE,
    MI_KW_TYPE,
    MI_KW_TIME
)
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_FORCE_UPDATE,
    CONF_MAC,
    CONF_MONITORED_CONDITIONS,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    EVENT_HOMEASSISTANT_START,
)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

CONF_PRODUCT_ID = "product_id"

DEFAULT_PRODUCT_ID = 275
DEFAULT_FORCE_UPDATE = False
DEFAULT_NAME = "Mi Kettle"
DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)

# Sensor types are defined like: Name, units, icon
SENSOR_TYPES = {
    MI_ACTION: ["Action", "", "mdi:state-machine"],
    MI_MODE: ["Mode", "", "mdi:settings-outline"],
    MI_SET_TEMPERATURE: ["Set temperature", "°C", "mdi:thermometer-lines"],
    MI_CURRENT_TEMPERATURE: ["Current temperature", "°C", "mdi:thermometer"],
    MI_KW_TYPE: ["Keep warm type", "", "mdi:thermostat"],
    MI_KW_TIME: ["Keep warm time", "s", "mdi:clock-outline"],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_MAC): cv.string,
        vol.Optional(CONF_MONITORED_CONDITIONS, default=list(SENSOR_TYPES)): vol.All(
            cv.ensure_list, [vol.In(SENSOR_TYPES)]
        ),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_PRODUCT_ID, default=DEFAULT_PRODUCT_ID): cv.positive_int,
        vol.Optional(CONF_FORCE_UPDATE, default=DEFAULT_FORCE_UPDATE): cv.boolean,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the MiKettle sensor."""
    cache = config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL).total_seconds()
    poller = MiKettle(config.get(CONF_MAC), config.get(CONF_PRODUCT_ID))

    force_update = config.get(CONF_FORCE_UPDATE)

    devs = []

    for parameter in config[CONF_MONITORED_CONDITIONS]:
        name = SENSOR_TYPES[parameter][0]
        unit = SENSOR_TYPES[parameter][1]
        icon = SENSOR_TYPES[parameter][2]

        prefix = config.get(CONF_NAME)
        if prefix:
            name = f"{prefix} {name}"

        devs.append(
            MiKettleSensor(poller, parameter, name, unit, icon, force_update)
        )

    async_add_entities(devs)


class MiKettleSensor(Entity):
    """Implementing the MiKettle sensor."""

    def __init__(self, poller, parameter, name, unit, icon, force_update):
        """Initialize the sensor."""
        self.poller = poller
        self.parameter = parameter
        self._unit = unit
        self._icon = icon
        self._name = name
        self._state = None
        self.data = []
        self._force_update = force_update

    async def async_added_to_hass(self):
        """Set initial state."""

        @callback
        def on_startup(_):
            self.async_schedule_update_ha_state(True)

        self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, on_startup)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return self._unit

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._icon

    @property
    def force_update(self):
        """Force update."""
        return self._force_update

    def update(self):
        """
        Update current conditions.
        """
        try:
            _LOGGER.debug("Polling data for %s", self.name)
            data = self.poller.parameter_value(self.parameter)
        except OSError as ioerr:
            _LOGGER.info("Polling error %s", ioerr)
            return
        except Exception as bterror:
            _LOGGER.info("Polling error %s", bterror)
            return

        if data is not None:
            _LOGGER.debug("%s = %s", self.name, data)
            self._state = data
        else:
            _LOGGER.info("Did not receive any data from Mi kettle %s", self.name)
            # Remove old data from median list or set sensor value to None
            # if no data is available anymore
            self._state = None
            return
