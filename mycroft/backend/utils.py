import os
import random
from os import makedirs, urandom
from os.path import join
import subprocess
import tarfile
from os.path import exists, dirname
from threading import Thread
import json
from socket import gethostname
from pyopenssl import crypto
import requests
import random
import base64
from sqlalchemy.ext.declarative import declarative_base
import pygeoip
_running_downloads = {}

__author__ = "Ohlandt"


Base = declarative_base()


def gen_api(user="demo_user", save=False):
    k = urandom(32)
    k = base64.urlsafe_b64encode(k)
    k = ""+str(k)
    if not exists(join(dirname(__file__), "database")):
        makedirs(join(dirname(__file__), "database"))
    if not exists(join(dirname(__file__), "database", "users.json")):
        users = {}
    else:
        with open(join(dirname(__file__), "database", "users.json"), "r") as f:
            users = json.load(f)
    while k in users.keys():
        k = gen_api(user)
    k = k[:-1]
    if save:
        users[k] = {"id": str(len(users)), "last_active": 0, "name": user}
        with open(join(dirname(__file__), "database", "users.json"), "w") as f:
            data = json.dumps(users)
            f.write(data)
    return k


def model_to_dict(obj):
    serialized_data = {c.key: getattr(obj, c.key) for c in obj.__table__.columns}
    return serialized_data


def props(cls):
    return [i for i in cls.__dict__.keys() if i[:1] != '_']


def load_commented_json(filename):
    """ Loads an JSON file, ignoring comments
    Supports a trivial extension to the JSON file format.  Allow comments
    to be embedded within the JSON, requiring that a comment be on an
    independent line starting with '//' or '#'.
    NOTE: A file created with these style comments will break strict JSON
          parsers.  This is similar to but lighter-weight than "human json"
          proposed at https://hjson.org
    Args:
        filename (str):  path to the commented JSON file
    Returns:
        obj: decoded Python object
    """
    with open(filename) as f:
        contents = f.read()

    return json.loads(uncomment_json(contents))


def uncomment_json(commented_json_str):
    """ Removes comments from a JSON string.
    Supporting a trivial extension to the JSON format.  Allow comments
    to be embedded within the JSON, requiring that a comment be on an
    independent line starting with '//' or '#'.
    Example...
       {
         // comment
         'name' : 'value'
       }
    Args:
        commented_json_str (str):  a JSON string
    Returns:
        str: uncommented, legal JSON
    """
    lines = commented_json_str.splitlines()
    # remove all comment lines, starting with // or #
    nocomment = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("#"):
            continue
        nocomment.append(line)

    return " ".join(nocomment)


def merge_dict(base, delta):
    """
        Recursively merging configuration dictionaries.
        Args:
            base:  Target for merge
            delta: Dictionary to merge into base
    """

    for k, dv in delta.items():
        bv = base.get(k)
        if isinstance(dv, dict) and isinstance(bv, dict):
            merge_dict(bv, dv)
        else:
            base[k] = dv


def geo_locate(ip):
    if ip in ["0.0.0.0", "127.0.0.1"]:
        response = requests.get("https://ipapi.co/json/")
        data = response.json()
        data["country_code"] = data["country"]
    else:
        g = pygeoip.GeoIP(join(root_dir(), 'database',
                                       'GeoLiteCity.dat'))
        data = g.record_by_addr(ip) or {}

    return data


def root_dir():
    """ Returns root directory for this project """
    return dirname(dirname(__file__))


def location_dict(city="", region_code="", country_code="",
             country_name="", region="", longitude=0, latitude=0,
             timezone="", **kwargs):
    region_data = {"code": region_code, "name": region,
                        "country": {
                            "code": country_code,
                            "name": country_name}}
    city_data = {"code": city, "name": city,
                      "state": region_data,
                      "region": region_data}
    timezone_data = {"code": timezone, "name": timezone,
                          "dstOffset": 3600000,
                          "offset": -21600000}
    coordinate_data = {"latitude": float(latitude),
                            "longitude": float(longitude)}
    return {"city": city_data,
                          "coordinate": coordinate_data,
                          "timezone": timezone_data}


def nice_json(arg):
    response = json.dumps(arg, sort_keys=True, indent=4)
    response.headers['Content-type'] = "application/json"
    return response


def create_self_signed_cert(cert_dir, name="mycroft"):
    """
    If name.crt and name.key don't exist in cert_dir, create a new
    self-signed cert and key pair and write them into that directory.
    """

    CERT_FILE = name + ".crt"
    KEY_FILE = name + ".key"
    cert_path = join(cert_dir, CERT_FILE)
    key_path = join(cert_dir, KEY_FILE)

    if not exists(join(cert_dir, CERT_FILE)) \
            or not exists(join(cert_dir, KEY_FILE)):
        # create a key pair
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 1024)

        # create a self-signed cert
        cert = crypto.X509()
        cert.get_subject().C = "PT"
        cert.get_subject().ST = "Europe"
        cert.get_subject().L = "Mountains"
        cert.get_subject().O = "Jarbas AI"
        cert.get_subject().OU = "Mycroft is <3"
        cert.get_subject().CN = gethostname()
        cert.set_serial_number(random.randint(0, 2000))
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha1')
        if not exists(cert_dir):
            makedirs(cert_dir)
        open(cert_path, "wb").write(
            crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        open(join(cert_dir, KEY_FILE), "wb").write(
            crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

    return cert_path, key_path


def _get_download_tmp(dest):
    tmp_base = dest + '.part'
    if not exists(tmp_base):
        return tmp_base
    else:
        i = 1
        while (True):
            tmp = tmp_base + '.' + str(i)
            if not exists(tmp):
                return tmp
            else:
                i += 1


class Downloader(Thread):
    """
        Downloader is a thread based downloader instance when instanciated
        it will download the provided url to a file on disk.
        When the download is complete or failed the `.done` property will
        be set to true and the `.status` will indicate the status code.
        200 = Success.
        Args:
            url:            Url to download
            dest:           Path to save data to
            complet_action: Function to run when download is complete.
                            `func(dest)`
    """

    def __init__(self, url, dest, complete_action=None, header=None):
        super(Downloader, self).__init__()
        self.url = url
        self.dest = dest
        self.complete_action = complete_action
        self.status = None
        self.done = False
        self._abort = False
        self.header = header

        # Create directories as needed
        if not exists(dirname(dest)):
            os.makedirs(dirname(dest))

        #  Start thread
        self.daemon = True
        self.start()

    def perform_download(self, dest):

        cmd = ['wget', '-c', self.url, '-O', dest,
               '--tries=20', '--read-timeout=5']
        if self.header:
            cmd += ['--header={}'.format(self.header)]
        return subprocess.call(cmd)

    def run(self):
        """
            Does the actual download.
        """
        tmp = _get_download_tmp(self.dest)
        self.status = self.perform_download(tmp)

        if not self._abort and self.status == 0:
            self.finalize(tmp)
        else:
            self.cleanup(tmp)
        self.done = True
        arg_hash = hash(self.url + self.dest)

        #  Remove from list of currently running downloads
        if arg_hash in _running_downloads:
            _running_downloads.pop(arg_hash)

    def finalize(self, tmp):
        """
            Move the .part file to the final destination and perform any
            actions that should be performed at completion.
        """
        os.rename(tmp, self.dest)
        if self.complete_action:
            self.complete_action(self.dest)

    def cleanup(self, tmp):
        """
            Cleanup after download attempt
        """
        if exists(tmp):
            os.remove(self.dest + '.part')
        if self.status == 200:
            self.status = -1

    def abort(self):
        """
            Abort download process
        """
        self._abort = True


def download(url, dest, complete_action=None, header=None):
    global _running_downloads
    arg_hash = hash(url + dest)
    if arg_hash not in _running_downloads:
        _running_downloads[arg_hash] = Downloader(url, dest, complete_action,
                                                  header)
    return _running_downloads[arg_hash]


def untar(file_path, dest, remove=False):
    if not exists(file_path):
        raise AssertionError("file does not exist")
    if not file_path.endswith(".tar.gz") or not file_path.endswith(".tar.bz2"):
        raise AssertionError("invalid file format")
    with tarfile.open(file_path) as tar:
        tar.extractall(dest)
    if remove:
        os.remove(file_path)
