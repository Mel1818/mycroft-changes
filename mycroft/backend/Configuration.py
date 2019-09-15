from mycroft.util.log import LOG
from os.path import exists, isfile
from os.path import join, expanduser, exists
from mycroft.backend.utils import load_commented_json
USER_CONFIG = join(expanduser('~'), '/mycroft/configuration/mycroft.conf')


def load_local(self):

    if exists(USER_CONFIG) and isfile(USER_CONFIG):
        try:
            config = load_commented_json(USER_CONFIG)
            for key in config:
                self.__setitem__(key, config[key])

            LOG.debug("Configuration {} loaded".format(USER_CONFIG))
        except Exception as e:
            LOG.error("Error loading configuration '{}'".format(USER_CONFIG))
            LOG.error(repr(e))
    else:
        LOG.debug("Configuration '{}' not defined, skipping".format(USER_CONFIG))
