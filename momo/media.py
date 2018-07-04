# -*- coding: utf-8 -*-
import time

try:
    from string import ascii_letters as letters, digits
except ImportError:
    from string import letters, digits
import random
from hashlib import md5
import urllib

from qiniu import Auth, BucketManager, put_file
from qcloud_cos import (CosConfig, CosS3Client,
                        CosServiceError, CosClientError)

from momo.helper import smart_str
from momo.settings import Config


def generate_nonce_str(length=32):
    return ''.join(random.SystemRandom().choice(
        letters + digits) for _ in range(length))


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


def media_fetch_to_qiniu(media_url, media_id):
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


def get_qiniu_token(key=None, bucket_name=None):
    q = qiniu_auth()
    bucket_name = bucket_name or Config.QINIU_BUCKET
    token = q.upload_token(bucket_name, key, 3600)
    return token


def upload_file_to_qiniu(file_path, key=None, **kwargs):
    bucket_name = kwargs.pop('bucket_name', None)
    token = get_qiniu_token(key, bucket_name=bucket_name)
    ret, info = put_file(token, key, file_path, **kwargs)
    return ret, info


def get_cos_client(secret_id=None, secret_key=None,
                   region=None, token=''):
    # 设置用户属性, 包括secret_id, secret_key, region
    secret_id = secret_id or Config.QCOS_SECRET_ID
    secret_key = secret_key or Config.QCOS_SECRET_KEY
    region = region or Config.QCOS_REGION
    token = ''                 # 使用临时秘钥需要传入Token，默认为空,可不填
    config = CosConfig(Region=region, Secret_id=secret_id,
                       Secret_key=secret_key, Token=token)  # 获取配置对象
    client = CosS3Client(config)
    return client


def upload_file_to_qcos(filepath, file_name, appid=None, bucket='note'):
    # 本地路径 简单上传
    appid = appid or Config.QCOS_APPID
    bucket = '%s-%s' % (bucket, appid)
    client = get_cos_client()
    response = client.put_object_from_local_file(
        Bucket=bucket,
        LocalFilePath=filepath,
        Key=file_name,
    )
    return response
