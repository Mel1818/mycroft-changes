from mycroft.backend.utils import nice_json, gen_api, model_to_dict
from tempfile import NamedTemporaryFile
from speech_recognition import Recognizer, AudioFile
from mycroft.backend.stt import STTFactory
import mycroft.backend.Configuration
import mycroft.configuration
import json
from os.path import join, dirname, expanduser, exists
from mycroft.util.log import LOG
DEFAULT_CONFIG = join(dirname(__file__), 'mycroft.conf')
USER_CONFIG = join(expanduser('~'), '.mycroft/mycroft.conf')
recognizer = Recognizer()
engine = STTFactory.create()


def pair(self):
    # pair
    result = {"paired": True}
    return nice_json(result)


def stt(language, limit, audio):
    flac_audio = audio
    lang = language
    with NamedTemporaryFile() as fp:
        fp.write(flac_audio)
        with AudioFile(fp.name) as source:
            audio = recognizer.record(source)  # read the entire audio file

        utterance = engine.execute(audio, language=lang)
    return json.dumps([utterance])


def setting():
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

    cleans += ["listener_energy_ratio", "record_wake_words",
               "record_utterances", "wake_word_upload",
               "stand_up_word",
               "wake_word", "listener_sample_rate",
               "listener_channels",
               "listener_multiplier", "phoneme_duration"]

    result["listener"] = {
        "sample_rate": config.listener.sample_rate,
        "record_wake_words": config.listener.record_wake_words,
        "phoneme_duration": config.listener.phoneme_duration,
        "wake_word_upload": {"enable": False},
        "multiplier": config.listener.multiplier,
        "wake_word": config.listener.wake_word,
        "stand_up_word": config.listener.stand_up_word
    }

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
    result["tts"] = {"module": tts.module,
                     tts.module: {"lang": tts.espeak.lang,
                                  "voice": tts.espeak.voice}}
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
    return json.dumps(result, sort_keys=True, indent=4)
