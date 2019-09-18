from mycroft.util.log import LOG
from os.path import exists, isfile
from os.path import join, expanduser, exists
from mycroft.backend.utils import load_commented_json
import inflection
import re
import mycroft.configuration
USER_CONFIG = join(expanduser('~'), '.mycroft/mycroft.conf')
# USER_CONFIG = join(expanduser('~'), '/mycroft/configuration/mycroft.conf')

class LocalConfig(dict):
    def __init__(self,cache=None):
        super(LocalConfig, self).__init__()
        mycroft.configuration.Configuration.load_config_stack([{}], True)
        local = mycroft.configuration.LocalConf(USER_CONFIG)
        config = mycroft.configuration.Configuration.load_config_stack([local], True)
        self.load(config)

    def load(self, config):
        for key in config:
            self.__setitem__(key, config[key])

