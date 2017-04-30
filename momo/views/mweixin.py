# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six import StringIO

import xmltodict
from flask import current_app as app, views
from flask import Blueprint, request, abort

from weixin import WeixinMpAPI
from weixin.reply import WXReply, TextReply, ArticleReply as _ArticleReply
from weixin.response import WXResponse as _WXResponse
from weixin.lib.WXBizMsgCrypt import WXBizMsgCrypt

from momo.settings import Config
from momo.helper import validate_xml, smart_str


blueprint = Blueprint('weixin', __name__, url_prefix='/weixin')

appid = smart_str(Config.WEIXINMP_APPID)
token = smart_str(Config.WEIXINMP_TOKEN)
encoding_aeskey = smart_str(Config.WEIXINMP_ENCODINGAESKEY)

AUTO_REPLY_CONTENT = """
Hi，朋友！

这是我妈四月的公号，我是魔魔，我可以陪你聊天呦！
"""

CUSTOMER_SERVICE_TEMPLATE = '''
<xml>
    <ToUserName><![CDATA[{to_user}]]></ToUserName>
    <FromUserName><![CDATA[{from_user}]]></FromUserName>
    <CreateTime>{create_time}</CreateTime>
    <MsgType><![CDATA[transfer_customer_service]]></MsgType>
</xml>
'''


class ReplyContent(object):

    _source = 'value'

    def __init__(self, event, keyword):
        self.event = event
        self.keyword = keyword
        if self.event == 'scan':
            pass

    @property
    def value(self):
        return ''


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

    def _text_msg_handler(self):
        # 文字消息处理逻辑
        self.reply_params['content'] = 'eeeeeee'
        self.reply = TextReply(**self.reply_params).render()
        content = self.data.get('Content')
        if content:
            print(content)

    def _click_event_handler(self):
        # 点击菜单事件的逻辑
        pass


class WXRequestView(views.MethodView):

    def _get_args(self):
        params = request.args.to_dict()
        if not params:
            abort(400)
        args = {
            'mp_token': app.config['WEIXINMP_TOKEN'],
            'signature': params.get('signature'),
            'timestamp': params.get('timestamp'),
            'echostr': params.get('echostr'),
            'nonce': params.get('nonce'),
        }
        return args

    def get(self):
        args = self._get_args()
        weixin = WeixinMpAPI(**args)
        if weixin.validate_signature():
            return args.get('echostr') or 'fail'
        return 'fail'

    def _get_xml(self):
        post_str = request.data
        # 验证xml 格式是否正确
        validate_xml(StringIO(post_str))
        return post_str

    def _decrypt_xml(self, crypt, xml_str):
        params = request.args.to_dict()
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

    def post(self):
        args = self._get_args()
        weixin = WeixinMpAPI(**args)
        if not weixin.validate_signature():
            raise AttributeError("Invalid weixin signature")
        xml_str = self._get_xml()
        crypt = WXBizMsgCrypt(token, encoding_aeskey, appid)
        decryp_xml, nonce = self._decrypt_xml(crypt, xml_str)
        xml_dict = xmltodict.parse(decryp_xml)
        xml = WXResponse(xml_dict)() or 'success'
        encryp_xml = self._encryp_xml(crypt, xml, nonce)
        return encryp_xml or xml


blueprint.add_url_rule('/request', endpoint='request',
                       view_func=WXRequestView.as_view('request'))
