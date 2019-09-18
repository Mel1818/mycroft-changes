from mycroft.backend.utils import nice_json, gen_api, model_to_dict
from tempfile import NamedTemporaryFile
from speech_recognition import Recognizer, AudioFile
from mycroft.backend.stt import STTFactory
from mycroft.backend.Configuration import load_local
import json
from mycroft.util.log import LOG
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
    config = load_local()
    result = config
    LOG.debug("MELISSA API: " + str(config))

    # format result
    cleans = ["skills_dir", "skills_auto_update"]

    blacklisted = [skill.folder for skill in config.skills
                   if
                   skill.blacklisted]
    priority = [skill.folder for skill in config.skills if
                skill.priority]

    result["skills"] = {"directory": config.skills_dir,
                        "auto_update": config.skills_auto_update,
                        "blacklisted_skills": blacklisted,
                        "priority_skills": priority}

    cleans += ["listener_energy_ratio", "record_wake_words",
               "record_utterances", "wake_word_upload",
               "stand_up_word",
               "wake_word", "listener_sample_rate",
               "listener_channels",
               "listener_multiplier", "phoneme_duration"]

    result["listener"] = {
        "sample_rate": result["listener_sample_rate"],
        "channels": result["listener_channels"],
        "record_wake_words": result["record_wake_words"],
        "record_utterances": result["record_utterances"],
        "phoneme_duration": result["phoneme_duration"],
        "wake_word_upload": {"enable": result["wake_word_upload"]},
        "multiplier": result["listener_multiplier"],
        "energy_ratio": result["listener_energy_ratio"],
        "wake_word": result["wake_word"],
        "stand_up_word": result["stand_up_word"]
    }

    result["sounds"] = {}
    for sound in config.sounds:
        result["sounds"][sound.name] = sound.path

    result["hotwords"] = {}
    for word in config.hotwords:
        result["hotwords"][word.name] = {
            "module": word.module,
            "phonemes": word.phonemes,
            "threshold": word.threshold,
            "lang": word.lang,
            "active": word.active,
            "listen": word.listen,
            "utterance": word.utterance,
            "sound": word.sound
        }
    stt = config.stt
    creds = {}
    if stt.engine_type == "token":
        creds = {"token": stt.token}
    elif stt.engine_type == "basic":
        creds = {"username": stt.username,
                 "password": stt.password}
    elif stt.engine_type == "key":
        creds = {"client_id": stt.client_id,
                 "client_key": stt.client_key}
    elif stt.engine_type == "json":
        creds = {"json": stt.client_id,
                 "client_key": stt.client_key}

    result["stt"] = {"module": stt.name,
                     stt.name: {"uri": stt.uri, "lang": stt.lang,
                                "credential": creds}
                     }

    tts = config.tts
    result["tts"] = {"module": tts.name,
                     tts.name: {"token": tts.token,
                                "lang": tts.lang,
                                "voice": tts.voice,
                                "gender": tts.gender,
                                "uri": tts.uri}}
    if tts.engine_type == "token":
        result["tts"][tts.name].merge({"token": tts.token})
    elif tts.engine_type == "basic":
        result["tts"][tts.name].merge({"username": tts.username,
                                       "password": tts.password})
    elif tts.engine_type == "key":
        result["tts"][tts.name].merge({"client_id": tts.client_id,
                                       "client_key": tts.client_key})
    elif tts.engine_type == "api":
        result["tts"][tts.name].merge({"api_key": tts.api_key})
    return nice_json(result)
