"""
Securitas platform that offers a control over alarm status.
"""
import logging
import voluptuous as vol

from homeassistant.util import convert
from homeassistant.components.switch import (SwitchDevice)
from homeassistant.const import (STATE_OFF, STATE_ON, CONF_NAME, CONF_SWITCHES)

#import requests
import time

from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING,
)

DOMAIN = 'securitas'
_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_devices, discovery_info=None):

    #my_name = config.get(CONF_NAME)
    #my_username = config.get(CONF_USERNAME)
    #my_password = config.get(CONF_PASSWORD)
    client = hass.data[DOMAIN]['client']
    name = hass.data[DOMAIN]['name']
    
    switchSecuritas = SecuritasSwitch(hass, name, client)
    add_devices([switchSecuritas])
    add_devices([SecuritasHomeModeSwitch(switchSecuritas)])


class SecuritasSwitch(SwitchDevice):

    def __init__(self, hass, name, client, mode=STATE_ALARM_ARMED_AWAY):
        _LOGGER.info("Initialized Securitas SWITCH %s", name)
        self._hass = hass
        self._hass.custom_attributes = {}
        self._name = name
        self._mode = STATE_ALARM_ARMED_AWAY
        self._icon = 'mdi:lock-open-outline'
        self._state = STATE_ALARM_DISARMED
        self._last_updated = 0
        self._client = client
        self.update()

    def _set_as_armed(self):
        if self._mode == STATE_ALARM_ARMED_AWAY:
            self._set_as_armed_away()
        else:
            self._set_as_armed_home()

    def _set_as_armed_away(self):
        self._last_updated = time.time()
        self._icon = 'mdi:lock'
        self._mode = STATE_ALARM_ARMED_AWAY

    def _set_as_armed_home(self):
        self._last_updated = time.time()
        self._icon = 'mdi:account-lock'
        self._mode = STATE_ALARM_ARMED_HOME

    def _set_as_disarmed(self):
        self._last_updated = time.time()
        self._icon = 'mdi:lock-open-outline'

    def _set_as_pending(self):
        self._last_updated = time.time()
        self._icon = 'mdi:lock-clock'
        self._state == STATE_ALARM_PENDING

    def turn_on(self, **kwargs):
        """Turn device on."""
        _LOGGER.debug("Update Securitas SWITCH to on, mode %s ", self._mode)
        self._client.set_alarm_status(self._mode)
        self._set_as_pending()
        
    def turn_off(self, **kwargs):
        """Turn device off."""
        _LOGGER.debug("Update Securitas SWITCH to off")
        self._client.set_alarm_status(STATE_ALARM_DISARMED)
        self._set_as_pending()

    def update(self):
        _LOGGER.debug("Updated Securitas SWITCH %s", self._name)
        diff = time.time() - self._last_updated
        
        if diff > 15:
            self._state = self._client.get_alarm_status()
            attributes = {}
            attributes['state'] = self._state
            self._hass.custom_attributes = attributes
            if self._state == STATE_ALARM_ARMED_AWAY:
                self._set_as_armed_away()
            elif self._state == STATE_ALARM_ARMED_HOME:
                self._set_as_armed_home()
            else:
                self._set_as_disarmed()

    @property
    def is_on(self):
        """Return true if device is on."""
        return (self._state == STATE_ALARM_ARMED_AWAY or self._state == STATE_ALARM_ARMED_HOME)

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._hass.custom_attributes

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def icon(self):
        return self._icon

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, m):
        self._mode = m

    @property
    def should_poll(self):
        """Polling is needed."""
        return True

class SecuritasHomeModeSwitch(SwitchDevice):

    def __init__(self, parentSwitch):
        self._parentSwitch = parentSwitch
        self._name = parentSwitch.name + " Home Mode"
        self._icon = 'mdi:account-lock-outline'
        self.update()

    def turn_on(self, **kwargs):
        """Turn device on."""
        self._parentSwitch.mode = STATE_ALARM_ARMED_HOME
        self._icon = 'mdi:account-lock'
        if self._parentSwitch.is_on:
            self._parentSwitch.turn_on()
            _LOGGER.debug("Toggled Securitas SWITCH to Home Mode")
        
        
    def turn_off(self, **kwargs):
        """Turn device off."""
        _LOGGER.debug("Update Securitas SWITCH to off")
        self._parentSwitch.mode = STATE_ALARM_ARMED_AWAY
        self._icon = 'mdi:account-lock-outline'
        if self._parentSwitch.is_on:
            self._parentSwitch.turn_on()
            _LOGGER.debug("Toggled Securitas SWITCH to Away Mode")
        

    def update(self):
        if self._parentSwitch.mode == STATE_ALARM_ARMED_HOME:
            self._icon = 'mdi:account-lock'
        else:
            self._icon = 'mdi:account-lock-outline'
    
        _LOGGER.debug("Updated Securitas SWITCH %s", self._name)
    
    @property
    def is_on(self):
        """Return true if device is on."""
        return self._parentSwitch.mode == STATE_ALARM_ARMED_HOME

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def icon(self):
        return self._icon

    @property
    def should_poll(self):
        """Polling is needed."""
        return True