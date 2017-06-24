# -*- coding: utf-8 -*-
import time

try:
    from string import ascii_letters as letters, digits
except ImportError:
    from string import letters, digits
import random
from six.moves.urllib.parse import urlparse
from hashlib import md5
import urllib
import requests
from requests.exceptions import ConnectTimeout, ReadTimeout

from qiniu import Auth, BucketManager

from momo.helper import smart_str
from momo.settings import Config


def generate_nonce_str(length=32):
    return ''.join(random.SystemRandom().choice(
        letters + digits) for _ in range(length))


def weixin_media_url(media_id):
    from momo.helper import get_weixinmp_token
    appid = Config.WEIXINMP_APPID
    app_secret = Config.WEIXINMP_APP_SECRET
    url = 'http://file.api.weixin.qq.com/cgi-bin/media/get?access_token=%s&media_id=%s'
    access_token, errors = get_weixinmp_token(appid, app_secret)
    if errors:
        return
    media_url = url % (access_token, media_id)
    return media_url


class QiniuUriGen():

    __version__ = '1.0'

    def __init__(self, access_key=None, secret_key=None,
                 time_key=None, host=None):
        self.access_key = access_key
        self.secret_key = secret_key
        self.time_key = time_key
        self.host = host

    def url_encode(self, s):
        if not s:
            return ''
        return urllib.quote(smart_str(s), safe="/")

    def t16(self, t):
        return hex(t)[2:].lower()

    def to_deadline(self, expires):
        return int(time.time()) + int(expires)

    def summd5(self, str):
        m = md5()
        m.update(str)
        return m.hexdigest()

    def sign(self, path, t):
        if not path:
            return
        key = self.time_key
        a = key + self.url_encode(path) + t
        sign_s = self.summd5(a).lower()
        sign_part = "sign=" + sign_s + "&t=" + t
        return sign_part

    def sign_download_url(self, path, expires=1800):
        deadline = self.to_deadline(expires)
        sign_part = self.sign('/%s' % path, self.t16(deadline))
        return '%s/%s?' % (self.host, path) + sign_part


def qiniu_sign_url(hash_key, expires=1800):
    config = Config.QINIU_AUDIOS_CONFIG
    url = QiniuUriGen(**config).sign_download_url(hash_key, expires)
    return url


class MediaInfo(object):

    def __init__(self, key):
        self.key = key
        self.url = qiniu_sign_url(key)

    def avinfo(self):
        url = '%s&avinfo' % self.url
        try:
            req = requests.get(url, timeout=(2, 2))
        except (ConnectTimeout, ReadTimeout):
            return {}
        if req.status_code == 200:
            info = req.json()
            return info.get('format', {})
        return {}

    @property
    def duration(self):
        avinfo = self.avinfo()
        if not avinfo:
            return 0
        duration = avinfo.get('duration', 0)
        try:
            duration = int(float(duration) + 0.5)
            return duration
        except ValueError:
            return 0

    @property
    def size(self):
        avinfo = self.avinfo()
        if not avinfo:
            return None
        size = avinfo.get('size', -1)
        try:
            size = int(size) / 1000
            return size
        except ValueError:
            return -1

    @property
    def md5(self):
        url = '%s&hash/md5' % self.url
        try:
            req = requests.get(url, timeout=(2, 2))
        except (ConnectTimeout, ReadTimeout):
            return ''
        if req.status_code == 200:
            info = req.json()
            return info.get('md5', '')
        return ''


def media_for(hash_key, scheme=None, style=None):
    if not hash_key:
        return None
    url = hash_key.split('!')[0]
    up = urlparse(url)
    hash_domain = up.hostname
    if hash_domain and hash_domain not in Config.QINIU_DOMAINS:
        if hash_domain == 'wx.qlogo.cn':
            hash_key = hash_key.replace('http://', 'https://')
        return hash_key
    _hash = up.path
    if len(_hash) != 0 and _hash[0] == '/':
        _hash = _hash[1:]

    media_host = Config.QINIU_HOST
    url = '%s/%s' % (media_host, _hash)
    if url.endswith('.amr'):
        url = '%s.mp3' % url[:-4]
    if url and style:
        url = '%s!%s' % (url, style)
    return url


def image_for(image, style=None, scheme=None):
    url = media_for(image, scheme=scheme, style=style)
    return url


def media_fetch(media_url, media_id):
    '''抓取url的资源存储在库'''
    auth = qiniu_auth()
    bucket = BucketManager(auth)
    bucket_name = Config.QINIU_BUCKET
    ret, info = bucket.fetch(media_url, bucket_name, media_id)
    if info.status_code == 200:
        return True, media_id
    return False, None


def qiniu_auth():
    access_key = str(Config.QINIU_ACCESS_TOKEN)
    secret_key = str(Config.QINIU_SECRET_TOKEN)
    auth = Auth(access_key, secret_key)
    return auth


def media_copy(key, from_bucket, to_bucket):
    auth = qiniu_auth()
    bucket = BucketManager(auth)
    ret, info = bucket.stat(from_bucket, key)
    if ret:
        ret, info = bucket.copy(from_bucket, key,
                                to_bucket, key)
    return ret, info


def qiniu_image_hash(hash_key):
    if not hash_key:
        return False, None
    url = hash_key.split('!')[0]
    up = urlparse(url)
    hash_domain = up.hostname
    if hash_domain and hash_domain not in Config.QINIU_DOMAINS:
        return False, hash_key
    _hash = up.path
    if len(_hash) != 0 and _hash[0] == '/':
        _hash = _hash[1:]
    return True, _hash
