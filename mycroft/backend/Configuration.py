from mycroft.util.log import LOG
from os.path import exists, isfile
from os.path import join, expanduser, exists
from mycroft.backend.utils import load_commented_json
import inflection
import re
import mycroft.configuration
from os.path import join, dirname, expanduser
DEFAULT_CONFIG = join(dirname(__file__), 'mycroft.conf')
USER_CONFIG = join(expanduser('~'), '.mycroft/mycroft.conf')
# USER_CONFIG = join(expanduser('~'), '/mycroft/configuration/mycroft.conf')

class LocalConfig(dict):
    def __init__(self, config):
        super(LocalConfig, self).__init__()
        self.load(config)

    def load(self, config):
        for k, v in config.items():
            if isinstance(v, (list, tuple)):
                setattr(self, k, [LocalConfig(x) if isinstance(x, dict) else x for x in v])
            else:
                setattr(self, k, LocalConfig(v) if isinstance(v, dict) else v)
