"""
Support for the Olympia Electronics Thermostat.

"""
import logging, json, requests, jwt, re, datetime

import voluptuous as vol

from homeassistant.components.climate import (
    ATTR_CURRENT_TEMPERATURE, ATTR_FAN_MODE, ATTR_HVAC_MODE,
    PLATFORM_SCHEMA, ClimateDevice)
from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO, HVAC_MODE_HEAT, HVAC_MODE_OFF, CURRENT_HVAC_IDLE, SUPPORT_TARGET_TEMPERATURE,
    CURRENT_HVAC_COOL, CURRENT_HVAC_HEAT, CURRENT_HVAC_OFF)
from homeassistant.const import (
    ATTR_TEMPERATURE, CONF_EMAIL, CONF_PASSWORD, CONF_TOKEN, TEMP_CELSIUS, PRECISION_HALVES,
    PRECISION_TENTHS, PRECISION_WHOLE)
import homeassistant.helpers.config_validation as cv


_LOGGER = logging.getLogger(__name__)

DOMAIN = "olympia_electronics"

CONF_MIN_TEMP = 'min_temp'
CONF_MAX_TEMP = 'max_temp'
CONF_PRECISION = 'precision'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_EMAIL): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_TOKEN): cv.string,
    vol.Optional(CONF_MIN_TEMP): vol.Coerce(float),
    vol.Optional(CONF_MAX_TEMP): vol.Coerce(float),
    vol.Optional(CONF_PRECISION): vol.In(
        [PRECISION_TENTHS, PRECISION_HALVES, PRECISION_WHOLE])
})

HA_STATE_TO_OLYMPIA = {
    HVAC_MODE_HEAT: 'on',
    HVAC_MODE_OFF: 'off',
    HVAC_MODE_AUTO: 'idle'
}

OLYMPIA_TO_HA_STATE = {
    'on': HVAC_MODE_HEAT,
    'off': HVAC_MODE_OFF,
    'idle': HVAC_MODE_AUTO
}


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Init platform"""
    _LOGGER.info("Setting up olympia electronics")

    _min_temp = config.get(CONF_MIN_TEMP)
    _max_temp = config.get(CONF_MAX_TEMP)
    _precision = config.get(CONF_PRECISION)
    cloud_email = config.get(CONF_EMAIL)
    cloud_password = config.get(CONF_PASSWORD)

    _headers = {
        'Content-Type'  : 'application/x-www-form-urlencoded'
    }
    _login_details = {
        'email'     : cloud_email,
        'password'  : cloud_password
    }

    r = requests.post('https://iot-api.olympia-electronics.gr/v1/users/login/',
                      headers=_headers, data=_login_details)

    resp = r.json()
    _LOGGER.debug("Got details %s",json.dumps(resp))

    if 'non_field_errors' in resp:
        _LOGGER.warning("Error logging in to Olympia Electronics Service: %s",resp['non_field_errors'])
        return

    _AUTH_TOKEN = resp['token']

    _headers = {
        'Authorization'  : 'JWT {}'.format(_AUTH_TOKEN)
    }

    r = requests.get('https://iot-api.olympia-electronics.gr/v1/thermostats/', headers=_headers)

    resp = r.json()
    _LOGGER.debug("Got thermostats %s",json.dumps(resp))
    entities = []

    for device in resp['results']:
        entity = OlympiaElectronicsThermostat(_login_details, device['id'], device['name'], device['status'], _min_temp, _max_temp, _precision, _AUTH_TOKEN)
        entities.append(entity)

    add_entities(entities)



class OlympiaElectronicsThermostat(ClimateDevice):
    """Representation of a Olympia Electronics Thermostat."""

    def __init__(self, login_details, id, name, status, min_temp, max_temp, precision, auth_token):
        self._support_flags = SUPPORT_TARGET_TEMPERATURE
        self._name = name
        self._login_details = login_details
        self._id = id
        self._AUTH_TOKEN = auth_token
        if min_temp:
            self._min_temp = min_temp
        else:
            self._min_temp = 10
        if max_temp:
            self._max_temp = config.get('CONF_MAX_TEMP')
        else:
            self._max_temp = 30
        if precision is not None:
            self._precision = precision
        else:
            self._precision = PRECISION_TENTHS
        self.setStatus(status)
        self._current_operation = None

    def setStatus(self ,status):
        self._temperature = status['temperature']
        self._is_on = status['is_on']
        self._boiler_on = status['boiler_on']
        self._target_temperature = status['setpoint']
        self._burner_on = status['burner_on']
        self._is_online = status['is_online']

    @property
    def supported_features(self):
        """Return the list of supported features."""
        """_LOGGER.debug('Called supported_features')"""
        return self._support_flags

    @property
    def should_poll(self):
        """Return the polling state."""
        """_LOGGER.debug('Called should_poll')"""
        return True

    @property
    def isValidToken(self):
        try:
            decToken = jwt.decode(self._AUTH_TOKEN, verify=False)
            dt = datetime.datetime.utcnow()
            if decToken.get('exp')<dt.timestamp():
                _LOGGER.warning('JWT EXPIRED')
                return False
            else:
                return True

        except jwt.exceptions.DecodeError as err:
            _LOGGER.error('JWT is invalid (%s): %s',err ,self._AUTH_TOKEN)
            return False

    @property
    def name(self):
        """_LOGGER.debug('Called name')"""
        return self._name

    def update(self):
        """Requested update"""
        """_LOGGER.debug('Called update')"""
        if not self.isValidToken:
            self.updateToken()
            if not self.isValidToken:
                _LOGGER.warning('Failed to fetch updated token')
                return

        _headers = {
            'Authorization'  : 'JWT {}'.format(self._AUTH_TOKEN)
        }

        _LOGGER.debug('Getting update from the thermostat api')
        r = requests.get('https://iot-api.olympia-electronics.gr/v1/thermostats/{}/'.format(self._id), headers=_headers)
        if r.status_code != 200:
            _LOGGER.error('Could not update! Got %d status code from olympia-electronics',r.status_code)
            if r.status_code == 401:
                self.updateToken()
                if not self.isValidToken:
                    _LOGGER.warning('Failed to fetch updated token')
                    return
        else:
            resp = r.json()
            _LOGGER.debug('Updated info from thermostat: %s',resp)
            self.setStatus(resp['status'])

    def updateToken(self):
        _headers = {
            'Content-Type'  : 'application/x-www-form-urlencoded'
        }

        r = requests.post('https://iot-api.olympia-electronics.gr/v1/users/login/',
                          headers=_headers, data=self._login_details)

        resp = r.json()
        _LOGGER.debug("Got details %s",json.dumps(resp))

        if 'non_field_errors' in resp:
            _LOGGER.warning("Error logging in to Olympia Electronics Service: %s",resp['non_field_errors'])
            return

        self._AUTH_TOKEN = resp['token']

    @property
    def temperature_unit(self):
        """_LOGGER.debug('Called temperature_unit')"""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        """_LOGGER.debug('Called current_temperature')"""
        return self._temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        """_LOGGER.debug('Called target_temperature')"""
        return self._target_temperature

    @property
    def hvac_mode(self):
        """Return current operation ie. heat, cool, idle."""
        _LOGGER.debug('requested hvac_mode: %s',self._is_on)
        if self._is_on:
            if self._burner_on:
                return HVAC_MODE_HEAT
            else:
                return HVAC_MODE_AUTO
        else:
            return HVAC_MODE_OFF

    def set_hvac_mode(self, operation_mode):
        _LOGGER.debug('Will set mode')
        state = HA_STATE_TO_OLYMPIA.get(operation_mode)
        if state is None:
            return
        _LOGGER.debug('Mode is not none')
        if state == 'on':
            self._target_temperature = self._temperature + 1
            _LOGGER.debug("Will set tempetature to {}".format(self._target_temperature))
            self._is_on = True
        elif state == 'off':
            _LOGGER.debug("Will turn thermo off")
            self._is_on = False
        self.sendUpdateToApi()

    @property
    def available(self) -> bool:
        """Return if thermostat is available."""
        """_LOGGER.debug('Called available')"""
        return True

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        """_LOGGER.debug('Called operation_list')"""
        return [HVAC_MODE_HEAT, HVAC_MODE_OFF, HVAC_MODE_AUTO]

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode."""
        """_LOGGER.debug('Called is_on')"""
        if self._is_on:
            return HVAC_MODE_HEAT
        return HVAC_MODE_OFF

#    @property
#    def current_operation(self):
#        """Return current operation ie. heat, cool, idle."""
#        _LOGGER.debug('requested current_operation: %s',self._current_operation)
#        return self._current_operation

    @property
    def hvac_action(self):
        """Return the current running hvac operation if supported.
        Need to be one of CURRENT_HVAC_*.
        """
        if self._is_on:
            if self._burner_on:
                return CURRENT_HVAC_HEAT
            else:
                return CURRENT_HVAC_IDLE
        else:
            return CURRENT_HVAC_OFF

    def sendUpdateToApi(self):
        if not self.isValidToken:
            self.updateToken()
            if not self.isValidToken:
                _LOGGER.error('Token failed to update. Sorry')
                return

        _headers = {
            'Authorization'  : 'JWT {}'.format(self._AUTH_TOKEN),
            'Content-Type'  : 'application/x-www-form-urlencoded'
        }
        ton = "off"
        if self._is_on:
            ton = "true"

        _post_data = {
            'turn_on'     : ton,
            'setpoint'    : "{}".format(self._target_temperature)
        }
        _LOGGER.debug('Will send new data to the api %s',_post_data)
        r = requests.put("https://iot-api.olympia-electronics.gr/v1/thermostats/{}/settings/".format(self._id),
                      headers=_headers, data=_post_data)
        _LOGGER.debug('Got reply %s',r.text)
        self.update()

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        """_LOGGER.debug('Called set_temperature')"""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self._target_temperature = kwargs.get(ATTR_TEMPERATURE)
        self.schedule_update_ha_state()
        self.sendUpdateToApi()

    def set_operation_mode(self, operation_mode):
        """Set new operation mode."""
        _LOGGER.debug('setting current_operation: %s',operation_mode)
        self._current_operation = operation_mode
        self.schedule_update_ha_state()

    def set_hvac_mode(self, hvac_mode):
        """Turn on."""
        if hvac_mode == HVAC_MODE_HEAT:
            self._is_on = True
        elif hvac_mode == HVAC_MODE_OFF:
            self._is_on = False
        else:
            _LOGGER.error("Unrecognized hvac mode: %s", hvac_mode)
            return
        self.schedule_update_ha_state()
        self.sendUpdateToApi()

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        """_LOGGER.debug('Called min_temp')"""
        return self._min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        """_LOGGER.debug('Called max_temp')"""
        return self._max_temp

    @property
    def precision(self):
        """Return the precision."""
        """_LOGGER.debug('Called precision')"""
        return self._precision
