from mycroft.util.log import LOG
from os.path import exists, isfile
from os.path import join, expanduser, exists
from mycroft.backend.utils import load_commented_json
import inflection
import re
import mycroft.configuration
USER_CONFIG = join(expanduser('~'), '.mycroft/mycroft.conf')
# USER_CONFIG = join(expanduser('~'), '/mycroft/configuration/mycroft.conf')

class LocalConfig:
    def __init__(self):
        super(LocalConfig, self).__init__(None)
        mycroft.configuration.Configuration.load_config_stack([{}], True)
        local = mycroft.configuration.LocalConf(USER_CONFIG)
        config = mycroft.configuration.Configuration.load_config_stack([local], True)

        for key in config:
            self.__setitem__(key, config[key])
        if exists(USER_CONFIG) and isfile(USER_CONFIG):
            try:
                LOG.debug("Configuration {} loaded".format(USER_CONFIG))
            except Exception as e:
                LOG.error("Error loading configuration '{}'".format(USER_CONFIG))
                LOG.error(repr(e))
        else:
            LOG.error("CONFIG not found")
            LOG.debug("Configuration '{}' not defined, skipping".format(USER_CONFIG))

