from mycroft.util.log import LOG
from os.path import exists, isfile
from os.path import join, expanduser, exists
from mycroft.backend.utils import load_commented_json
USER_CONFIG = join(expanduser('~'), 'mycroft-changes/mycroft/configuration/mycroft.conf')


def load_local():

    if exists(USER_CONFIG) and isfile(USER_CONFIG):
        try:
            result = {}
            config = load_commented_json(USER_CONFIG)
            for key in config:
                result[key] =config[key]
                LOG.debug(key)

            LOG.debug("Configuration {} loaded".format(USER_CONFIG))
        except Exception as e:
            LOG.error("Error loading configuration '{}'".format(USER_CONFIG))
            LOG.error(repr(e))
    else:

        LOG.debug("Configuration '{}' not defined, skipping".format(USER_CONFIG))
    return result
