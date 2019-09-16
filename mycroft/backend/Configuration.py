from mycroft.util.log import LOG
from os.path import exists, isfile
from os.path import join, expanduser, exists
from mycroft.backend.utils import load_commented_json
import inflection
import re
import mycroft.configuration
USER_CONFIG = join(expanduser('~'), 'mycroft-changes/mycroft/configuration/mycroft.conf')


def load_local():

    if exists(USER_CONFIG) and isfile(USER_CONFIG):
        try:
            mycroft.configuration.Configuration.load_config_stack([{}], True)
            config = mycroft.configuration.LocalConf(USER_CONFIG)
            LOG.debug("Configuration {} loaded".format(USER_CONFIG))
        except Exception as e:
            LOG.error("Error loading configuration '{}'".format(USER_CONFIG))
            LOG.error(repr(e))
    else:

        LOG.debug("Configuration '{}' not defined, skipping".format(USER_CONFIG))
    return config
