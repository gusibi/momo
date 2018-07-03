from os import environ, path
from six.moves.urllib.parse import urlparse


class Config(object):

    DEBUG = False
    TESTING = False

    SECRET_KEY = 'MmPNFrWjQZ3Z9yKZ8PMFQttgHphaq8AZ'

    MONGO_MASTER_HOST = environ.get('MONGO_PORT_27017_TCP_ADDR', '127.0.0.1')
    MONGO_MASTER_PORT = environ.get('MONGO_PORT_27017_TCP_PORT', '27017')
    MONGO_DATABASE = environ.get('MONGO_DATABASE', 'momo_bill')
    MONGO_MASTER_URL = 'mongodb://%s:%s' % (MONGO_MASTER_HOST,
                                            MONGO_MASTER_PORT)

    APP_TRANSPORT = environ.get('APP_TRANSPORT', 'http')
    APP_DOMAIN = environ.get('APP_DOMAIN', 'http://gusibi.com')
    API_DOMAIN = environ.get('API_DOMAIN', 'http://gusibi.com')
    DOMAIN = '%s://%s' % (APP_TRANSPORT, urlparse(APP_DOMAIN).netloc)

    # 微信 公众账号信息
    WEIXINMP_APPID = environ.get('WEIXINMP_APPID', 'appid')
    WEIXINMP_APP_SECRET = environ.get('WEIXINMP_APP_SECRET', '')
    WEIXINMP_TOKEN = environ.get('WEIXINMP_TOKEN', 'token')
    WEIXINMP_ENCODINGAESKEY = environ.get(
        'WEIXINMP_ENCODINGAESKEY', '')

    PM25_TOKEN = environ.get('PM25_TOKEN', 'pm25_token')
    XMR_ID = environ.get('XMR_ID', '')

    QINIU_ACCESS_TOKEN = environ.get('QINIU_ACCESS_TOKEN', '')
    QINIU_SECRET_TOKEN = environ.get('QINIU_SECRET_TOKEN', '')
    QINIU_UPLOAD_URL = 'http://up.qiniu.com/'
    QINIU_DOMAIN = environ.get('QINIU_DOMAIN', 'media.gusibi.mobi')
    QINIU_DOMAINS = [QINIU_DOMAIN, 'omuo4kh1k.bkt.clouddn.com']
    QINIU_HOST = "http://%s" % QINIU_DOMAIN
    QINIU_NOTIFY_URL = '%s/qiniu/pfop/notify' % DOMAIN
    QINIU_BUCKET = environ.get('QINIU_BUCKET', 'blog')

    QINIU_AUDIOS_TIME_KEY = environ.get('QINIU_AUDIOS_TIME_KEY', '')
    QINIU_AUDIOS_HOST = environ.get('QINIU_AUDIOS_HOST',
                                    'http://omuo4kh1k.bkt.clouddn.com')

    QINIU_AUDIOS_CONFIG = {
        'access_key': QINIU_ACCESS_TOKEN,
        'secret_key': QINIU_SECRET_TOKEN,
        'time_key': QINIU_AUDIOS_TIME_KEY,
        'host': QINIU_AUDIOS_HOST
    }

    NOTE_OTF = path.normpath(path.join(
        path.dirname(__file__), 'note_imgs/SourceHanSansSC-Regular.otf'))
    NOTE_SIZE = 660
    if NOTE_SIZE == 990:
        NOTE_HEADER_FILE = 'note_header.png'
        NOTE_FOOTER_FILE = 'note_footer.png'
        NOTE_BODY_FILE = 'note_body.png'
        NOTE_WIDTH = 990
        NOTE_TEXT_WIDTH = 760
        NOTE_BODY_HEIGHT = 309
        NOTE_HEADER_HEIGHT = 133
        NOTE_FOOTER_HEIGHT = 218
    else:
        NOTE_HEADER_FILE = 'note_header_660.png'
        NOTE_FOOTER_FILE = 'note_footer_660.png'
        NOTE_BODY_FILE = 'note_body_660.png'
        NOTE_WIDTH = 660
        NOTE_TEXT_WIDTH = 460
        NOTE_BODY_HEIGHT = 206
        NOTE_HEADER_HEIGHT = 89
        NOTE_FOOTER_HEIGHT = 145

    NOTE_HEADER_IMG = path.normpath(path.join(
        path.dirname(__file__), 'note_imgs/%s' % NOTE_HEADER_FILE))
    NOTE_BODY_IMG = path.normpath(path.join(
        path.dirname(__file__), 'note_imgs/%s' % NOTE_BODY_FILE))
    NOTE_FOOTER_IMG = path.normpath(path.join(
        path.dirname(__file__), 'note_imgs/%s' % NOTE_FOOTER_FILE))
