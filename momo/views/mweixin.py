# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six import StringIO

import re
import xmltodict
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer

from sanic import Blueprint
from sanic.views import HTTPMethodView
from sanic.response import text
from sanic.exceptions import ServerError

from weixin import WeixinMpAPI
from weixin.reply import WXReply, TextReply, ArticleReply as _ArticleReply
from weixin.response import WXResponse as _WXResponse
from weixin.lib.WXBizMsgCrypt import WXBizMsgCrypt

from momo.settings import Config
from momo.helper import validate_xml, smart_str
from momo.media import media_fetch, weixin_media_url
from momo.models.wx_response import KWResponse as KWR


blueprint = Blueprint('weixin', url_prefix='/weixin')

appid = smart_str(Config.WEIXINMP_APPID)
token = smart_str(Config.WEIXINMP_TOKEN)
encoding_aeskey = smart_str(Config.WEIXINMP_ENCODINGAESKEY)

AUTO_REPLY_CONTENT = """
Hi，朋友！

这是我妈四月的公号，我是魔魔，我可以陪你聊天呦！

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

momo_chat = ChatBot(
    'Momo',
    storage_adapter='chatterbot.storage.MongoDatabaseAdapter',
    logic_adapters=[
        "chatterbot.logic.BestMatch",
        "chatterbot.logic.MathematicalEvaluation",
        "chatterbot.logic.TimeLogicAdapter",
    ],
    input_adapter='chatterbot.input.VariableInputTypeAdapter',
    output_adapter='chatterbot.output.OutputAdapter',
    database='chatterbot',
    read_only=True
)



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
            response = momo_chat.get_response(self.content)
            if isinstance(response, str):
                return response
            return response.text
        return ''

    def set(self, conversation):
        if self.momo:
            momo_chat.set_trainer(ListTrainer)
            momo_chat.train(conversation)
            return '魔魔学会了！'


class CustomerService(WXReply):

    """
    回复客服消息
    """
    TEMPLATE = CUSTOMER_SERVICE_TEMPLATE

    def __init__(self, *args, **kwargs):
        super(CustomerService, self).__init__(*args, **kwargs)

    def render(self):
        return self.TEMPLATE.format(**self.params)


class Article(object):

    def __init__(self, Title=None, Description=None, PicUrl=None, Url=None):
        self.title = Title or ''
        self.description = Description or ''
        self.picurl = PicUrl or ''
        self.url = Url or ''


class ArticleReply(_ArticleReply):

    def add_article(self, article):
        if len(self._articles) >= 10:
            raise AttributeError("Can't add more than 10 articles in an ArticleReply")
        else:
            self._articles.append(article)


class WXResponse(_WXResponse):

    auto_reply_content = AUTO_REPLY_CONTENT

    def _subscribe_event_handler(self):
        content = ReplyContent('subscribe', 'subscribe')
        self.reply_params['content'] = content.value or self.auto_reply_content
        self.reply = TextReply(**self.reply_params).render()

    def _unsubscribe_event_handler(self):
        pass

    def _unsub_scan_event_handler(self):
        event_key = self.data.get('EventKey')[8:]
        content = ReplyContent('scan', event_key)
        if content.type == 'article':
            article_reply = ArticleReply(**self.reply_params)
            values = content.value
            for value in values:
                article = Article(**value)
                article_reply.add_article(article)
            self.reply = article_reply.render()
        elif content.type == 'text' or not content.type:
            self.reply_params['content'] = content.value
            self.reply = TextReply(**self.reply_params).render()

    def _scan_event_handler(self):
        # 扫描带参数的二维码 关注的处理方法
        event_key = self.data.get('EventKey')
        content = ReplyContent('scan', event_key)
        if not content.value:
            return
        if content.type == 'article':
            article_reply = ArticleReply(**self.reply_params)
            values = content.value
            for value in values:
                article = Article(**value)
                article_reply.add_article(article)
            self.reply = article_reply.render()
        elif content.type == 'text' or not content.type:
            self.reply_params['content'] = content.value
            self.reply = TextReply(**self.reply_params).render()
        else:
            return

    def _image_msg_handler(self):
        media_id = self.data['MediaId']
        # 个人订阅号不支持
        # picurl = weixin_media_url(media_id)
        picurl = None
        if not picurl:
            picurl = self.data['PicUrl']
        is_succeed, media_key = media_fetch(picurl, media_id)
        qiniu_url = '{host}/{key}'.format(host=Config.QINIU_HOST, key=media_key)
        self.reply_params['content'] = qiniu_url
        self.reply = TextReply(**self.reply_params).render()

    def _text_msg_handler(self):
        # 文字消息处理逻辑
        event_key = 'text'
        content = self.data.get('Content')
        match = momo_learn.match(content)
        if match:
            conversation = match.groups()
            reply_content = ReplyContent('text', event_key)
            response = reply_content.set(conversation)
            self.reply_params['content'] = response
        else:
            kwr = KWR('gs', content)
            value = kwr.get_response()
            if not value:
                reply_content = ReplyContent('text', event_key, content)
                value = reply_content.value
            print(value, type(value))
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
