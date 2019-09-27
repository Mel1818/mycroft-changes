import mock
import json
from unittest import TestCase
import mycroft.configuration
from os.path import join, dirname
from mycroft.backend.utils import nice_json
DEFAULT_CONFIG = join(dirname(__file__), 'mycroft.conf')


class TestConfiguration(TestCase):
    def setUp(self):
        """
            Clear cached configuration
        """
        super(TestConfiguration, self).setUp()
        mycroft.configuration.Configuration.load_config_stack([{}], True)

    def test_get(self):
        d1 = {'a': 1, 'b': {'c': 1, 'd': 2}}
        d2 = {'b': {'d': 'changed'}}
        d = mycroft.configuration.Configuration.get([d1, d2])
        self.assertEquals(d['a'], d1['a'])
        self.assertEquals(d['b']['d'], d2['b']['d'])
        self.assertEquals(d['b']['c'], d1['b']['c'])

    @mock.patch('mycroft.api.DeviceApi')
    def test_remote(self, mock_api):
        remote_conf = {'TestConfig': True, 'uuid': 1234}
        remote_location = {'city': {'name': 'Stockholm'}}
        dev_api = mock.MagicMock()
        dev_api.get_settings.return_value = remote_conf
        dev_api.get_location.return_value = remote_location
        mock_api.return_value = dev_api

        rc = mycroft.configuration.RemoteConf()
        self.assertTrue(rc['test_config'])
        self.assertEquals(rc['location']['city']['name'], 'Stockholm')

    @mock.patch('json.dump')
    @mock.patch('mycroft.configuration.config.exists')
    @mock.patch('mycroft.configuration.config.isfile')
    @mock.patch('mycroft.configuration.config.load_commented_json')
    def test_local(self, mock_json_loader, mock_isfile, mock_exists,
                   mock_json_dump):
        local_conf = {'answer': 42, 'falling_objects': ['flower pot', 'whale']}
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_json_loader.return_value = local_conf
        lc = mycroft.configuration.LocalConf('test')
        self.assertEquals(lc, local_conf)

        # Test merge method
        merge_conf = {'falling_objects': None, 'has_towel': True}
        lc.merge(merge_conf)
        self.assertEquals(lc['falling_objects'], None)
        self.assertEquals(lc['has_towel'], True)

        # test store
        lc.store('test_conf.json')
        self.assertEquals(mock_json_dump.call_args[0][0], lc)
        # exists but is not file
        mock_isfile.return_value = False
        lc = mycroft.configuration.LocalConf('test')
        self.assertEquals(lc, {})

        # does not exist
        mock_exists.return_value = False
        lc = mycroft.configuration.LocalConf('test')
        self.assertEquals(lc, {})

    def test_backend(self):
        local = mycroft.configuration.LocalConf(DEFAULT_CONFIG)
        temp = mycroft.configuration.Configuration.load_config_stack([local], True)
        config = mycroft.backend.Configuration.LocalConfig(temp)
        result = config
        # format result
        cleans = ["skills_dir", "skills_auto_update"]

        blacklisted = [skill.folder for skill in config.skills
                       if
                       skill.blacklisted]
        priority = [skill.folder for skill in config.skills if
                    skill.priority]

        result["skills"] = {"directory": config.skills_dir,
                            "auto_update": False,
                            "blacklisted_skills": blacklisted,
                            "priority_skills": priority}
        self.assertIsNotNone(result["skills"])

        cleans += ["listener_energy_ratio", "record_wake_words",
                   "record_utterances", "wake_word_upload",
                   "stand_up_word",
                   "wake_word", "listener_sample_rate",
                   "listener_channels",
                   "listener_multiplier", "phoneme_duration"]
        self.assertIsNotNone(cleans)

        result["listener"] = {
            "sample_rate": config.listener.sample_rate,
            "record_wake_words": config.listener.record_wake_words,
            "phoneme_duration": config.listener.phoneme_duration,
            "wake_word_upload": {"enable": False},
            "multiplier": config.listener.multiplier,
            "wake_word": config.listener.wake_word,
            "stand_up_word": config.listener.stand_up_word
        }
        self.assertIsNotNone(result["listener"])

        result["sounds"] = {}
        for sound in config.sounds:
            result["sounds"][sound.name] = sound.path

        result["hotwords"] = {}
        for word in temp["hotwords"]:
            result["hotwords"][word] = {
                "module": temp["hotwords"][word]["module"],
                "phonemes": temp["hotwords"][word]["phonemes"],
                "threshold": temp["hotwords"][word]["threshold"],
                "lang": temp["hotwords"][word]["lang"]
            }
        stt = config.stt
        creds = {}
        # if stt.engine_type == "token":
        #     creds = {"token": stt.token}
        # elif stt.engine_type == "basic":
        #     creds = {"username": stt.username,
        #              "password": stt.password}
        # elif stt.engine_type == "key":
        #     creds = {"client_id": stt.client_id,
        #              "client_key": stt.client_key}
        # elif stt.engine_type == "json":
        #     creds = {"json": stt.client_id,
        #              "client_key": stt.client_key}

        result["stt"] = {"module": stt.module}
                         # stt.name: {"uri": stt.uri, "lang": stt.lang,
                         #            "credential": creds}
                         # }
        tts = config.tts
        result["tts"] = {"module": tts.module,tts.module: {"lang": tts.espeak.lang, "voice": tts.espeak.voice}}
        # if tts.engine_type == "token":
        #     result["tts"][tts.name].merge({"token": tts.token})
        # elif tts.engine_type == "basic":
        #     result["tts"][tts.name].merge({"username": tts.username,
        #                                    "password": tts.password})
        # elif tts.engine_type == "key":
        #     result["tts"][tts.name].merge({"client_id": tts.client_id,
        #                                    "client_key": tts.client_key})
        # elif tts.engine_type == "api":
        #     result["tts"][tts.name].merge({"api_key": tts.api_key})
        mainresult = json.dumps(result, sort_keys=True, indent=4)
        self.assertIsNotNone(mainresult)

    @mock.patch('mycroft.configuration.config.RemoteConf')
    @mock.patch('mycroft.configuration.config.LocalConf')
    def test_update(self, mock_remote, mock_local):
        mock_remote.return_value = {}
        mock_local.return_value = {'a': 1}
        c = mycroft.configuration.Configuration.get()
        self.assertEquals(c, {'a': 1})

        mock_local.return_value = {'a': 2}
        mycroft.configuration.Configuration.updated('message')
        self.assertEquals(c, {'a': 2})

    def tearDown(self):
        mycroft.configuration.Configuration.load_config_stack([{}], True)
