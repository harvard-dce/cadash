# -*- coding: utf-8 -*-
"""dce ca models."""

from jinja2 import Template
import json

from cadash.inventory.errors import MissingConfigSettingError
from cadash.inventory.models import AkamaiStreamingConfig
from cadash.inventory.models import Ca
from cadash.inventory.models import EpiphanChannel
from cadash.inventory.models import EpiphanRecorder
from cadash.inventory.models import Location
from cadash.inventory.models import LocationConfig
from cadash.inventory.models import MhCluster
from cadash.inventory.models import MhpearlConfig
from cadash.inventory.models import Role
from cadash.inventory.models import RoleConfig
from cadash.inventory.models import Vendor
from cadash.inventory.models import VendorConfig


# default dce source layout for channel
# (separate channels for presenter and presentation)
SINGLE_CHANNEL_LAYOUT_TEMPLATE = Template('''{
    "audio": [
        {
            "settings": {
                "source": "{{source_id}}.{{aconnector}}-{{ainput}}-audio"
            },
            "type": "source"
        }
    ],
    "background": "#000000",
    "nosignal": {
        "id": "default"
    },
    "video": [
        {
            "position": {
                "height": "100%",
                "keep_aspect_ratio": true,
                "left": "0%",
                "top": "0%",
                "width": "100%"
            },
            "settings": {
                "source": "{{source_id}}.{{vconnector}}-{{vinput}}"
            },
            "type": "source"
        }
    ]
}
''')

# default dce source layout for live channel
# (combined presenter and presentation in same channel)
COMBINED_CHANNELS_LAYOUT_TEMPLATE = Template('''{
    "audio": [
        {
            "settings": {
                "source": "{{source_id}}.{{pr_aconnector}}-{{pr_ainput}}-audio"
            },
            "type": "source"
        }
    ],
    "nosignal": {
        "id": "default"
    },
    "background": "#000000",
    "video": [
        {
            "crop": {},
            "position": {
                "keep_aspect_ratio": true,
                "height": "100%",
                "width": "50%",
                "left": "0%",
                "top": "0%"
            },
            "settings": {
                "source": "{{source_id}}.{{pr_vconnector}}-{{pr_vinput}}"
            },
            "type": "source"
        },
        {
            "crop": {},
            "position": {
                "keep_aspect_ratio": true,
                "height": "100%",
                "width": "50%",
                "left": "50%",
                "top": "0%"
            },
            "settings": {
                "source": "{{source_id}}.{{pn_vconnector}}-{{pn_vinput}}"
            },
            "type": "source"
        }
    ]
}''')


class DceConfigForEpiphanCaFactory(object):
    """put together a DceConfigForEpiphanCa."""

    @classmethod
    def retrieve(cls, ca_id):
        """."""
        ca = Ca.get_by_id(ca_id)
        if ca.role is not None:
            if ca.role.config is None:
                role_config = RoleConfig(ca.role)  # create cfg
            cfg = DceConfigForEpiphanCa(ca.role.config)
            return cfg
        return None


class DceConfigForEpiphanCa(object):
    """a capture agent dce-custom config for epiphan-pearl.

    wrapper over RoleConfig to apply some DCE business logic
    on how to set a base configuration for an epiphan-pearl
    capture agent.
    """

    def __init__(self, ca_config):
        """create instance, based on RoleConfig ca_config."""
        self.config = ca_config

        # create recorders, channels, mhpearl if not there
        if not self.config.recorders:
            self.create_dce_recorder()
        if not self.config.channels:
            self.create_dce_channels()
        if not self.config.mhpearl:
            self.create_dce_mhpearl()


    @property
    def ca(self):
        return self.config.ca

    @property
    def role_name(self):
        return self.ca.role.name

    @property
    def vendor(self):
        return self.ca.vendor

    @property
    def vendor_cfg(self):
        return self.vendor.config

    @property
    def location(self):
        return self.config.role.location

    @property
    def location_cfg(self):
        return self.location.config

    @property
    def cluster(self):
        return self.config.role.cluster

    @property
    def channels(self):
        return self.config.channels

    @property
    def recorders(self):
        return self.config.recorders

    @property
    def mhpearl(self):
        return self.config.mhpearl

    @property
    def channel_default_cfg(self):
        # default dce values for encoding
        return {
                'dce_live': {
                    'flavor': 'live',
                    'stream_cfg': None,
                    'encodings': {
                        'audiobitrate': 96,
                        'framesize': '1920x540',
                        'vbitrate': 4000,
                        },
                    },
                'dce_live_lowbr': {
                    'flavor': 'live',
                    'stream_cfg': None,
                    'encodings': {
                        'audiobitrate': 64,
                        'framesize': '960x270',
                        'vbitrate': 250,
                        },
                    },
                'dce_pr': {
                    'flavor': 'pr',
                    'stream_cfg': None,
                    'encodings': {
                        'audiobitrate': 160,
                        'framesize': '1280x720',
                        'vbitrate': 9000,
                        },
                    },
                'dce_pn': {
                    'flavor': 'pn',
                    'stream_cfg': None,
                    'encodings': {
                        'audiobitrate': 160,
                        'framesize': '1920x1080',
                        'vbitrate': 9000,
                        },
                    },
                }

    @property
    def connectors(self):
        # dynamic because there might be changes in location!
        return {
            'primary': {
                'pr': {
                    'vconnector': self.location.config.primary_pr_vconnector,
                    'vinput': self.location.config.primary_pr_vinput,
                    },
                'pn': {
                    'vconnector': self.location.config.primary_pn_vconnector,
                    'vinput': self.location.config.primary_pn_vinput,
                    },
                },
            'secondary': {
                'pr': {
                    'vconnector': self.location.config.secondary_pr_vconnector,
                    'vinput': self.location.config.secondary_pr_vinput,
                    },
                'pn': {
                    'vconnector': self.location.config.secondary_pn_vconnector,
                    'vinput': self.location.config.secondary_pn_vinput,
                    },
                },
            }

    def create_dce_recorder(self):
        """create and config channels for a dce ca."""
        rec = EpiphanRecorder.create(
                name=self.location.name_id,
                epiphan_config=self.config)
        # for now, defaults are enough!


    def create_dce_channels(self):
        """create and config channels for a dce ca."""
        # populate channel_cfg with stream config for live channels
        self.find_stream_cfg()

        for channel_name in self.channel_default_cfg.keys():
            # create channel in model
            chan = EpiphanChannel.create(
                    name=channel_name,
                    epiphan_config=self.config,
                    stream_cfg=self.channel_default_cfg[channel_name]['stream_cfg'])

            params = {}
            # config layout for input sources
            flavor = self.channel_default_cfg[channel_name]['flavor']
            if flavor == 'live':
                connector = self.connectors[self.role_name]
                l = COMBINED_CHANNELS_LAYOUT_TEMPLATE.render(
                        source_id=self.ca.capture_card_id,
                        pr_vconnector=connector['pr']['vconnector'],
                        pr_vinput=connector['pr']['vinput'],
                        pn_vconnector=connector['pn']['vconnector'],
                        pn_vinput=connector['pn']['vinput'],
                        pr_aconnector=connector['pr']['vconnector'],
                        pr_ainput=connector['pr']['vinput'])
            else:
                connector = self.connectors[self.role_name][flavor]
                l = SINGLE_CHANNEL_LAYOUT_TEMPLATE.render(
                        source_id=self.ca.capture_card_id,
                        vconnector=connector['vconnector'],
                        vinput=connector['vinput'],
                        # assume that audio always come from presenter
                        aconnector=self.connectors[self.role_name]['pr']['vconnector'],
                        ainput=self.connectors[self.role_name]['pr']['vinput'])

            params['source_layout'] = l.replace(' ', '').replace('\n', '')
            params.update(self.channel_default_cfg[channel_name]['encodings'])
            chan.update(**params)


    def find_stream_cfg(self):
        """define some criteria to pick stream config for live channels."""
        scfg_list = AkamaiStreamingConfig.query.all()
        stream_cfg = None
        for s in scfg_list:
            if 'prod' in s.name:
                stream_cfg = s
                break
        self.channel_default_cfg['dce_live']['stream_cfg'] = stream_cfg
        self.channel_default_cfg['dce_live_lowbr']['stream_cfg'] = stream_cfg


    def create_dce_mhpearl(self):
        """configure mhpearl."""
        MhpearlConfig.create(epiphan_config=self.config)


    @property
    def epiphan_dce_config(self):
        """return a dce_config for an epiphan-pearl ca as dict."""

        # validation
        if self.ca.capture_card_id is None:
            raise MissingConfigSettingError(
                    'config failed - ca({}), missing capture_card_id'.format(
                        self.ca.name_id))

        config = {}
        config['ca_capture_card_id'] = self.ca.capture_card_id
        config['ca_name_id'] = self.ca.name_id
        config['ca_serial_number'] = self.ca.serial_number
        config['ca_url'] = self.ca.address
        # take defaults from any already configure channel
        chan = self.channels[0]
        config['channel_encodings'] = {
                'audio': 'on' if chan.audio else '',
                'audiochannels': chan.audiochannels,
                'audiopreset': chan.audiopreset,
                'autoframesize': 'on' if chan.autoframesize else '',
                'codec': chan.codec,
                'fpslimit': chan.fpslimit,
                'vencpreset': chan.vencpreset,
                'vkeyframeinterval': chan.vkeyframeinterval,
                'vprofile': chan.vprofile,
                }
        channels = {}
        for chan in self.channels:
            cfg = {}
            if chan.channel_id_in_device > 99998:
                raise MissingConfigSettingError(
                        'config failed - ca({}), missing channel_id({})'.format(
                            self.ca.name_id, chan.name))
            else:
                cfg['channel_id'] = chan.channel_id_in_device
            cfg['encodings'] = {
                    'audio': 'on' if chan.audio else '',
                    'audiobitrate': chan.audiobitrate,
                    'audiochannels': chan.audiochannels,
                    'audiopreset': chan.audiopreset,
                    'autoframesize': chan.autoframesize,
                    'codec': chan.codec,
                    'fpslimit': chan.fpslimit,
                    'framesize': chan.framesize,
                    'vbitrate': chan.vbitrate,
                    'vencpreset': chan.vencpreset,
                    'vkeyframeinterval': chan.vkeyframeinterval,
                    'vprofile': chan.vprofile,
                    'source_layout': json.loads(chan.source_layout),
                    }
            if chan.stream_cfg is not None:
                if self.role_name == 'primary':
                    str_tpl = Template(chan.stream_cfg.primary_url_jinja2_template)
                else:  # role is secondary or experimental
                    str_tpl = Template(chan.stream_cfg.secondary_url_jinja2_template)
                cfg['rtmp_url'] = str_tpl.render(
                        stream_id=chan.stream_cfg.stream_id)
                str_name_tpl = Template(chan.stream_cfg.stream_name_jinja2_template)
                cfg['stream_name'] = str_name_tpl.render(
                        location_name=self.location.name_id,
                        framesize=cfg['encodings']['framesize'],
                        stream_id=chan.stream_cfg.stream_id)
            channels[chan.name] = cfg
        config['channels'] = channels
        config['cluster_env'] = self.cluster.env
        config['cluster_name_id'] = self.cluster.name_id
        config['firmware_version'] = self.vendor_cfg.firmware_version
        config['location_name_id'] = self.location.name_id
        config['mh_admin_url'] = self.cluster.admin_host
        config['mh_ca_name'] = self.location.name_id
        config['mhpearl_file_search_range'] = self.mhpearl.file_search_range_in_sec
        config['mhpearl_update_frequency'] = self.mhpearl.update_frequency_in_sec
        config['mhpearl_version'] = self.mhpearl.mhpearl_version
        config['role'] = self.role_name
        if self.vendor_cfg.source_deinterlacing:
            config['source_deinterlacing'] = 'on'
        else:
            config['source_deinterlacing'] = ''
        if self.vendor_cfg.maintenance_permanent_logs:
            config['maintenance'] = {'permanent_logs': 'on'}
        else:
            config['maintenance'] = {'permanent_logs': ''}
        recorders = {}
        for rec in self.recorders:
            cfg = {}
            if rec.recorder_id_in_device > 99998:
                raise MissingConfigSettingError(
                        'config failed - ca({}), missing recorder_id({})'.format(
                            self.ca.name_id, rec.name))
            else:
                cfg['recorder_id'] = rec.recorder_id_in_device
            cfg['output_format'] = rec.output_format
            cfg['sizelimit'] = rec.size_limit_in_kbytes
            cfg['timelimit'] = rec.time_limit_in_minutes
            recorders[rec.name] = cfg
        config['recorders'] = recorders
        config['touchscreen'] = {
                'episcreen_timeout': self.vendor_cfg.touchscreen_timeout_secs}
        return config





