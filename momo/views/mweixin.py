# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six import StringIO

import re
import time
import xmltodict
# from chatterbot.trainers import ListTrainer

import requests
from sanic import Blueprint
from sanic.views import HTTPMethodView
from sanic.response import text
from sanic.exceptions import ServerError

from weixin import WeixinMpAPI
from weixin.reply import TextReply, ImageReply
from weixin.response import WXResponse as _WXResponse
from weixin.lib.WXBizMsgCrypt import WXBizMsgCrypt

from momo.settings import Config
from momo.media import media_fetch_to_qiniu, upload_file_to_qcos
from momo.helper import (validate_xml, smart_str,
                         get_momo_answer, set_momo_answer,
                         get_weixinmp_token, get_weixinmp_media_id)
from momo.models.wx_response import KWResponse as KWR


blueprint = Blueprint('weixin', url_prefix='/weixin')

appid = smart_str(Config.WEIXINMP_APPID)
secret = smart_str(Config.WEIXINMP_APP_SECRET)
token = smart_str(Config.WEIXINMP_TOKEN)
encoding_aeskey = smart_str(Config.WEIXINMP_ENCODINGAESKEY)

PM25_BASE_URL = 'http://api.waqi.info'
PM25_TOKEN = Config.PM25_TOKEN

AUTO_REPLY_CONTENT = """
Hi，朋友！

这是我妈四月的公号，我是魔魔，我可以陪你聊天呦！

你可以输入"pm25 城市名" 查询实时 pm 指数！

也可以试试"菜单"、"note"、"并发"、"协程"、"设计模式" 等关键字吼！

<a href="https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=MzAwNjI5MjAzNw==&scene=124#wechat_redirect">历史记录</a>
"""

CUSTOMER_SERVICE_TEMPLATE = '''
<xml>
    <ToUserName><![CDATA[{to_user}]]></ToUserName>
    <FromUserName><![CDATA[{from_user}]]></FromUserName>
    <CreateTime>{create_time}</CreateTime>
    <MsgType><![CDATA[transfer_customer_service]]></MsgType>
</xml>
'''

momo_learn = re.compile(r'^momoya:"(?P<ask>\S*)"<"(?P<answer>\S*)"')
pm25 = re.compile(r'^pm25 (?P<city>\S*)')
xmr_url = 'https://supportxmr.com/api/miner/%s/stats' % Config.XMR_ID
xmr_stats_tmp = '''
Hash Rate(24 Avg): {hash}H/s ({lastHash}H/s)
Total Hashes: {totalHashes}
Valid Shares: {validShares}
Total Due: {amtDue} XMR
Total Paid: {amtPaid} XMR
'''


def get_response(url, format='json'):
    resp = requests.get(url)
    if resp.status_code != 200:
        return '发生了错误'
    if format == 'json':
        results = resp.json()
        return results


def get_pm25(city):
    url = "{}/search/?token={token}&keyword={city}".format(PM25_BASE_URL, token=PM25_TOKEN, city=city)
    results = get_response(url)
    if not isinstance(results, dict):
        return results
    data = results.get('data')
    if len(data) == 0:
        return '没有搜到结果'
    text = '\n'.join(['PM2.5: {pm25}  {name}'.format(
        name=info.get('station').get('name', '').split(';')[0],
        pm25=info.get('aqi')) for info in data])
    return text


def format_xmr_stats(data):
    data['lastHash'] = data.get('lastHash', 0) // (10**7)
    data['amtDue'] = data.get('amtDue', 0.0) / (10**12)
    return data


def get_xmr_stats():
    results = get_response(xmr_url)
    if not isinstance(results, dict):
        return results
    data = format_xmr_stats(results)
    text = xmr_stats_tmp.format(**data)
    return text


class ReplyContent(object):

    _source = 'value'

    def __init__(self, event, keyword, content=None, momo=True):
        self.momo = momo
        self.event = event
        self.content = content
        self.keyword = keyword
        if self.event == 'scan':
            pass

    @property
    def value(self):
        if self.momo:
            answer = get_momo_answer(self.content)
            return answer
        return ''

    def set(self, conversation):
        if self.momo:
            set_momo_answer(conversation)
            return '魔魔学会了！'


class Article(object):

    def __init__(self, Title=None, Description=None, PicUrl=None, Url=None):
        self.title = Title or ''
        self.description = Description or ''
        self.picurl = PicUrl or ''
        self.url = Url or ''


class WXResponse(_WXResponse):

    auto_reply_content = AUTO_REPLY_CONTENT

    def _subscribe_event_handler(self):
        self.reply_params['content'] = self.auto_reply_content
        self.reply = TextReply(**self.reply_params).render()

    def _unsubscribe_event_handler(self):
        pass

    def _image_msg_handler(self):
        media_id = self.data['MediaId']
        picurl = None
        if not picurl:
            picurl = self.data['PicUrl']
        is_succeed, media_key = media_fetch_to_qiniu(picurl, media_id)
        qiniu_url = '{host}/{key}'.format(host=Config.QINIU_HOST, key=media_key)
        self.reply_params['content'] = qiniu_url
        self.reply = TextReply(**self.reply_params).render()

    def _text_msg_handler(self):
        # 文字消息处理逻辑
        event_key = 'text'
        content = self.data.get('Content')
        pm25_match = pm25.match(content)
        learn_match = momo_learn.match(content)
        if learn_match:
            # 教魔魔说话第一优先级
            conversation = learn_match.groups()
            reply_content = ReplyContent('text', event_key)
            response = reply_content.set(conversation)
            self.reply_params['content'] = response
        elif pm25_match:
            # pm2.5 查询第二优先级
            city = pm25_match.groupdict().get('city')
            reply_content = ReplyContent('text', event_key)
            text = get_pm25(city)
            self.reply_params['content'] = text
        elif content.startswith('note '):
            if content.startswith('note -u '):
                note = content[8:]
            else:
                note = content[5:]
            reply_content = ReplyContent('text', event_key)
            to_user = self.reply_params['to_user']
            from momo.note import Note, note_img_config
            filename = '%s_%s.png' % (to_user, int(time.time()))
            note_file = Note(note, filename, **note_img_config).draw_text()
            if content.startswith('note -u '):
                upload_file_to_qcos(note_file, filename)
                qiniu_url = '{host}/{key}'.format(host=Config.QCOS_HOST,
                                                  key=filename)
                self.reply_params['content'] = qiniu_url
            else:
                access_token, _ = get_weixinmp_token(appid, secret)
                media_id = get_weixinmp_media_id(access_token, note_file)
                self.reply_params['media_id'] = media_id
                self.reply = ImageReply(**self.reply_params).render()
                return
        elif content == 'xmr_stats':
            text = get_xmr_stats()
            self.reply_params['content'] = text
        else:
            # 再查询有没有特殊自动回复消息workflow
            to_user = self.reply_params['to_user']
            kwr = KWR(to_user, content)
            value = kwr.get_response()
            if not value:
                reply_content = ReplyContent('text', event_key, content)
                value = reply_content.value
            if value.startswith('The current time is'):
                value = content
            self.reply_params['content'] = value
        self.reply = TextReply(**self.reply_params).render()

    def _click_event_handler(self):
        # 点击菜单事件的逻辑
        pass


class WXRequestView(HTTPMethodView):

    def _get_args(self, request):
        params = request.raw_args
        if not params:
            raise ServerError("invalid params", status_code=400)
        args = {
            'mp_token': Config.WEIXINMP_TOKEN,
            'signature': params.get('signature'),
            'timestamp': params.get('timestamp'),
            'echostr': params.get('echostr'),
            'nonce': params.get('nonce'),
        }
        return args

    def get(self, request):
        args = self._get_args(request)
        weixin = WeixinMpAPI(**args)
        if weixin.validate_signature():
            return text(args.get('echostr') or 'fail')
        return text('fail')

    def _get_xml(self, data):
        post_str = smart_str(data)
        # 验证xml 格式是否正确
        validate_xml(StringIO(post_str))
        return post_str

    def _decrypt_xml(self, params, crypt, xml_str):
        nonce = params.get('nonce')
        msg_sign = params.get('msg_signature')
        timestamp = params.get('timestamp')
        ret, decryp_xml = crypt.DecryptMsg(xml_str, msg_sign,
                                           timestamp, nonce)
        return decryp_xml, nonce

    def _encryp_xml(self, crypt, to_xml, nonce):
        to_xml = smart_str(to_xml)
        ret, encrypt_xml = crypt.EncryptMsg(to_xml, nonce)
        return encrypt_xml

    def post(self, request):
        args = self._get_args(request)
        weixin = WeixinMpAPI(**args)
        if not weixin.validate_signature():
            raise AttributeError("Invalid weixin signature")
        xml_str = self._get_xml(request.body)
        crypt = WXBizMsgCrypt(token, encoding_aeskey, appid)
        decryp_xml, nonce = self._decrypt_xml(request.raw_args, crypt, xml_str)
        xml_dict = xmltodict.parse(decryp_xml)
        xml = WXResponse(xml_dict)() or 'success'
        encryp_xml = self._encryp_xml(crypt, xml, nonce)
        return text(encryp_xml or xml)


blueprint.add_route(WXRequestView.as_view(), '/request')
