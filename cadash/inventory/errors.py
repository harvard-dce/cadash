# -*- coding: utf-8 -*-
"""exceptions in inventory module."""

from cadash.errors import Error


class InvalidMhClusterEnvironmentError(Error):
    """mh cluster environment value is invalid."""


class InvalidActionForCaStateError(Error):
    """action not allowed to be performed with ca in current state."""


class InvalidCaRoleError(Error):
    """role must be in cadash.inventory.models.CA_ROLES."""


class InvalidCaStateError(Error):
    """state must be in cadash.inventory.models.CA_STATES."""


class InvalidChannelNameForRecorderSetupError(Error):
    """channel_name must be part of CA list of channels."""


class InvalidEmptyValueError(Error):
    """value must be not_empty."""


class InvalidJsonValueError(Error):
    """value is not valid json."""


class InvalidOperationError(Error):
    """can't execute given operation in this object."""


class InvalidTimezoneError(Error):
    """timezone value is invalid."""


class AssociationError(Error):
    """can't associate entities due to some constraint."""


class MissingConfigSettingError(Error):
    """config setting is missing; can't generate a full config object."""


class MissingVendorError(Error):
    """vendor is not in inventory."""


class DuplicateCaptureAgentNameError(Error):
    """ca name already in inventory."""


class DuplicateCaptureAgentAddressError(Error):
    """ca address already in inventory."""


class DuplicateCaptureAgentSerialNumberError(Error):
    """ca serial_number already in inventory."""


class DuplicateLocationNameError(Error):
    """location name already in inventory."""


class DuplicateVendorNameModelError(Error):
    """vendor name-model name already in inventory."""


class DuplicateMhClusterNameError(Error):
    """mhcluster name name already in inventory."""


class DuplicateMhClusterAdminHostError(Error):
    """mhcluster admin_host name already in inventory."""


class DuplicateEpiphanChannelError(Error):
    """epiphan channel name already configured for this CA."""


class DuplicateEpiphanChannelIdError(Error):
    """epiphan channel_id_in_device already configured for this CA."""


class DuplicateEpiphanRecorderError(Error):
    """epiphan channel name already configured for this CA."""


class DuplicateEpiphanRecorderIdError(Error):
    """epiphan channel_id_in_device already configured for this CA."""


class DuplicateAkamaiStreamIdError(Error):
    """akamai stream_id already exist in inventory."""
