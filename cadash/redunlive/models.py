# -*- coding: utf-8 -*-
"""models for redunlive module."""
import arrow
import logging

from cadash import utils


class CaptureAgent(object):
    """
    object to proxy a epiphan-pearl device livestream status.

    the device is the source of truth, and when unreachable, the proxy status
    is 'not available'
    """

    def __init__(self, serial_number, address, firmware_version=3):
        self._serial_number = serial_number
        self._address = address
        self.firmware_version = firmware_version
        if firmware_version == "3":
            self.param = "publish_type"      # 6 (rtmp) or otherwise
        else: # In version 4, publish_type is always set, publish_enabled turns it on
            self.param = "publish_enabled"   # "on" or otherwise

        (name, trash) = self.address.split('.', 1)
        self._name = self.clean_name(name)

        self.client = None
        self._last_update = arrow.get(2000, 1, 1)

        # for now, the livestream channel# must be set externally
        # In 4.x livestream on = publish_type == 6 and enabled == "on"
        # In 3.x livestream on = publish_type == 6 
        self.channels = {
                'live': {
                    'channel': 'not available',
                    self.param: 'not available'},
                'lowBR': {
                    'channel': 'not available',
                    self.param: 'not available'},
            }


    @staticmethod
    def clean_name(name):
        return utils.clean_name(name)


    @property
    def serial_number(self):
        return self._serial_number


    @property
    def address(self):
        return self._address


    @property
    def last_update(self):
        return self._last_update


    @property
    def name(self):
        return self._name


    def __get_channel_publish_status(self, chan_name):
        chan = self.channels[chan_name]

        logger = logging.getLogger(__name__)
        logger.debug(
                'device(%s) channel(%s) is (%s)' %
                (self.name, chan_name, chan['channel']))

        if chan['channel'] == 'not available' or self.client is None:
            return 'not available'

        try:
            response = self.client.get_params(
                    channel=chan['channel'], params={self.param: ''})
            self._last_update = arrow.utcnow()

            logger.debug(
                    'device(%s) channel(%s)=(%s) %s=(%s)' %
                    (self.name, chan_name, chan['channel'], self.param, response))

        except Exception as e:
            logger.warning(
                    'CA(%s) unable to get channel(%s) %s. error: %s' %
                    (self.name, chan_name, self.param, e.message))

            return 'not available'
        else:
            return response[self.param] \
                    if self.param in response else 'not available'

    def __set_channel_publish_status(self, chan_name, value):
        chan = self.channels[chan_name]
        if chan['channel'] == 'not available' or self.client is None:
            return 'not available'

        logger = logging.getLogger(__name__)
        try:
            self.client.set_params(
                    channel=self.channels[chan_name]['channel'],
                    params={self.param: value})
            self._last_update = arrow.utcnow()
        except Exception as e:
            logger.warning(
                    'CA(%s) unable to set channel(%s) %s to %s. error: %s'
                    % (self.name, chan_name, value, self.param, e.message))
            return 'not available'

        else:
            logger.warning(
                    'CA(%s) channel(%s) %s set to %s'
                    % (self.name, chan_name, self.param, value))
            return value


    def sync_live_status(self):
        """
        refresh status of local object with info from capture agent.

        read publish_type from capture agent, both 'live' and 'lowBR' channels,
        and refresh status of local object
        if channels have diverging live status, try to set 'lowBR' publish_type
        as the same as 'live'
        """
        logger = logging.getLogger(__name__)
        logger.debug('in sync_live_status for device(%s)' % self.name)
        live = self.__get_channel_publish_status('live')
        lowBR = self.__get_channel_publish_status('lowBR')

        if live == lowBR:
            self.channels['live'][self.param] = live
            self.channels['lowBR'][self.param] = lowBR
        else:
            logger.warning(
                    'CA(%s) %s for live/lowBR (%s/%s); trying to fix...'
                    % (self.name, self.param, live, lowBR))
            value = self.__set_channel_publish_status('lowBR', live)

            if value == live:
                logger.warning(
                        'CA(%s) %s for live/lowBR fixed (%s)'
                        % (self.name, self.param, value))
            else:
                logger.warning(
                        'CA(%s) unable to fix %s for lowBR to (%s)'
                        % (self.name, self.param, live))

            # finally set channels to whatever was possible to set
            self.channels['live'][self.param] = live
            self.channels['lowBR'][self.param] = value


    def write_live_status(self, publish_stat):
        """set capture agent live status for both 'live' and 'lowBR' channels."""
        for ch in ['live','lowBR']:
            self.channels[ch][self.param] = \
                self.__set_channel_publish_status(ch, publish_stat)
        return publish_stat

    def write_live_status_enabled(self, publish_stat):
        """set capture agent live status for both 'live' and 'lowBR' channels."""
        for ch in ['live','lowBR']:
            self.channels[ch][self.param] = \
                self.__set_channel_publish_enabled(ch, publish_stat)
        return publish_stat

        # not ideal, but check that live and lowBR have the correct publish_type
        # is left to the user...


    def __repr__(self):
        return u'%s_%s' % (self._name, self._serial_number)


    # for debug purposes!
    def debug_print(self):
        return """CaptureAgent: %s
        serial_number: %s
        address:       %s
        live_channel:  %s
        live_status:   %s
        lowBR_channel: %s
        lowBR_status:  %s
        last_update:   %s
        """ % (self._name,
               self._serial_number,
               self._address,
               self.channels['live']['channel'],
               self.channels['live']['publish_type'],
               self.channels['lowBR']['channel'],
               self.channels['lowBR']['publish_type'],
               self.channels['live']['publish_enabled'],
               self.channels['lowBR']['publish_enabled'],
               self._last_update.to('local').format('YYYY-MM-DD HH:mm:ss ZZ'))



class CaLocation(object):

    def __init__(self, name, firmware_version="3"):
        self._id = self.clean_name(name)
        self._primary_ca = None
        self._secondary_ca = None
        self.firmware = firmware_version
        if firmware_version=="3":
            self.param = "publish_type"
            self.active = '6'
        else:
            self.param = "publish_enabled"
            self.active = 'on'

        self.name = name
        self.experimental_cas = []


    @staticmethod
    def clean_name(name):
        return utils.clean_name(name)


    @property
    def id(self):
        return self._id


    @property
    def primary_ca(self):
        return self._primary_ca

    @primary_ca.setter
    def primary_ca(self, primary):
        if not isinstance(primary, CaptureAgent):
            raise TypeError('arg "primary" must be of type "CaptureAgent"')

        self._primary_ca = primary
        if self._secondary_ca and self._secondary_ca.serial_number == primary.serial_number:
            raise ValueError('same capture agent for primary and secondary not allowed')


    @property
    def secondary_ca(self):
        return self._secondary_ca

    @secondary_ca.setter
    def secondary_ca(self, secondary):
        if not isinstance(secondary, CaptureAgent):
            raise TypeError('arg "secondary" must be of type "CaptureAgent"')

        self._secondary_ca = secondary
        if self._primary_ca and self._primary_ca.serial_number == secondary.serial_number:
            raise ValueError('same capture agent for secondary AND primary not allowed')


    @property
    def active_livestream(self):
        if self._primary_ca is not None:
            if self._primary_ca.channels['live'][self.param] == self.active:
                return 'primary'

        if self._secondary_ca is not None:
            if self._secondary_ca.channels['live'][self.param] == self.active:
                return 'secondary'

        # there's no active livestream
        return None


    def __repr__(self):
        return self._id


    # for debug purposes
    def debug_print(self):
        s = """Location: %s
        active_livestream: %s
        """ % (self._id,
               self.active_livestream)

        s += """primary_ca: %s
        secondary_ca: %s
        experimental_ca: [
        """ % (self.primary_ca.debug_print(), self.secondary_ca.debug_print())

        for c in self.experimental_cas:
            s += c.debug_print()
        s += ']'
        return s
