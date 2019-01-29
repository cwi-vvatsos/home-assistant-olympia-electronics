"""
Support for the Olympia Electronics Thermostat.

"""
import logging, json, requests, jwt, re, datetime

import voluptuous as vol

from homeassistant.components.climate import (
    ATTR_CURRENT_TEMPERATURE, ATTR_FAN_MODE, ATTR_OPERATION_MODE,
    ATTR_SWING_MODE, PLATFORM_SCHEMA, STATE_AUTO, STATE_COOL, STATE_DRY,
    STATE_FAN_ONLY, STATE_HEAT, STATE_OFF, SUPPORT_FAN_MODE, STATE_IDLE,
    SUPPORT_OPERATION_MODE, SUPPORT_ON_OFF, SUPPORT_TARGET_TEMPERATURE,
    ClimateDevice)
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
    STATE_HEAT: 'on',
    STATE_OFF: 'off',
    STATE_IDLE: 'idle'
}

OLYMPIA_TO_HA_STATE = {
    'on': STATE_HEAT,
    'off': STATE_OFF,
    'idle': STATE_IDLE
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
    _LOGGER.info("Got details %s",json.dumps(resp))

    if 'non_field_errors' in resp:
        _LOGGER.warning("Error logging in to Olympia Electronics Service: %s",resp['non_field_errors'])
        return

    _AUTH_TOKEN = resp['token']

    _headers = {
        'Authorization'  : 'JWT {}'.format(_AUTH_TOKEN)
    }

    r = requests.get('https://iot-api.olympia-electronics.gr/v1/thermostats/', headers=_headers)

    resp = r.json()
    _LOGGER.info("Got thermostats %s",json.dumps(resp))
    entities = []

    for device in resp['results']:
        entity = OlympiaElectronicsThermostat(_login_details, device['id'], device['name'], device['status'], _min_temp, _max_temp, _precision, _AUTH_TOKEN)
        entities.append(entity)

    add_entities(entities)



class OlympiaElectronicsThermostat(ClimateDevice):
    """Representation of a Olympia Electronics Thermostat."""

    def __init__(self, login_details, id, name, status, min_temp, max_temp, precision, auth_token):
        self._support_flags = SUPPORT_TARGET_TEMPERATURE | SUPPORT_ON_OFF | SUPPORT_OPERATION_MODE
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
#        _LOGGER.info('Called supported_features')
        return self._support_flags

    @property
    def should_poll(self):
        """Return the polling state."""
#        _LOGGER.info('Called should_poll')
        return True

    @property
    def isValidToken(self):
        try:
            decToken = jwt.decode(self._AUTH_TOKEN, verify=False)
            dt = datetime.datetime.utcnow()
            if decToken.get('exp')<dt.timestamp():
                _LOGGER.info('JWT EXPIRED')
                return False
            else:
                return True

        except jwt.exceptions.DecodeError as err:
            _LOGGER.info('JWT is invalid (%s): %s',err ,self._AUTH_TOKEN)
            return False

    @property
    def name(self):
#        _LOGGER.info('Called name')
        return self._name

    def update(self):
        """Requested update"""
#        _LOGGER.info('Called update')
        if not self.isValidToken:
            self.updateToken()
            if not self.isValidToken:
                _LOGGER.info('Failed to fetch updated token')
                return

        _headers = {
            'Authorization'  : 'JWT {}'.format(self._AUTH_TOKEN)
        }

        r = requests.get('https://iot-api.olympia-electronics.gr/v1/thermostats/{}/'.format(self._id), headers=_headers)
        if r.status_code != 200:
            _LOGGER.error('Could not update! Got %d status code from olympia-electronics',r.status_code)
        else:
            resp = r.json()
            self.setStatus(resp['status'])

    def updateToken(self):
        _headers = {
            'Content-Type'  : 'application/x-www-form-urlencoded'
        }

        r = requests.post('https://iot-api.olympia-electronics.gr/v1/users/login/',
                          headers=_headers, data=self._login_details)

        resp = r.json()
        _LOGGER.info("Got details %s",json.dumps(resp))

        if 'non_field_errors' in resp:
            _LOGGER.warning("Error logging in to Olympia Electronics Service: %s",resp['non_field_errors'])
            return

        self._AUTH_TOKEN = resp['token']

    @property
    def temperature_unit(self):
#        _LOGGER.info('Called temperature_unit')
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
#        _LOGGER.info('Called current_temperature')
        return self._temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
#        _LOGGER.info('Called target_temperature')
        return self._target_temperature

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
#        _LOGGER.info('Called current_operation')
        if self._is_on:
            if self._burner_on:
                return STATE_HEAT
            else:
                return STATE_IDLE
        else:
            return STATE_OFF

    def set_operation_mode(self, operation_mode):
        _LOGGER.info('Will set mode')
        state = HA_STATE_TO_OLYMPIA.get(operation_mode)
        if state is None:
            return
        _LOGGER.info('Mode is not none')
        if state == 'on':
            self._target_temperature = self._temperature + 1
            _LOGGER.info("Will set tempetature to {}".format(self._target_temperature))
            self._is_on = True
        elif state == 'off':
            _LOGGER.info("Will turn thermo off")
            self._is_on = False
        self.sendUpdateToApi()

    @property
    def available(self) -> bool:
        """Return if thermostat is available."""
#        _LOGGER.info('Called available')
        return self.current_operation is not None

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
#        _LOGGER.info('Called operation_list')
        return [STATE_HEAT,STATE_OFF, STATE_IDLE]

    @property
    def is_on(self):
        """Return true if the device is on."""
#        _LOGGER.info('Called is_on')
        return self._is_on

    def sendUpdateToApi(self):
        if not self.isValidToken:
            self.updateToken()
            if not self.isValidToken:
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

        r = requests.put("https://iot-api.olympia-electronics.gr/v1/thermostats/{}/settings/".format(self._id),
                      headers=_headers, data=_post_data)
        self.update()

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
#        _LOGGER.info('Called set_temperature')
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self._target_temperature = kwargs.get(ATTR_TEMPERATURE)
        self.sendUpdateToApi()

    def turn_on(self):
        """Turn on."""
#        _LOGGER.info('Called turn_on')
        self._is_on = True
        self.sendUpdateToApi()

    def turn_off(self):
        """Turn off."""
#        _LOGGER.info('Called turn_off')
        self._is_on = False
        self.sendUpdateToApi()

    @property
    def min_temp(self):
        """Return the minimum temperature."""
#        _LOGGER.info('Called min_temp')
        return self._min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature."""
#        _LOGGER.info('Called max_temp')
        return self._max_temp

    @property
    def precision(self):
        """Return the precision."""
#        _LOGGER.info('Called precision')
        return self._precision
