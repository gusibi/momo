# -*- coding: utf-8 -*-
from datetime import datetime

from sanic import Sanic, Blueprint
from sanic.views import HTTPMethodView
from sanic.response import text

from momo.models.bill import Tag
from momo.helper import get_momo_answer
from momo.models.wx_response import KWResponse as KWR


blueprint = Blueprint('index', url_prefix='/')


class Index(HTTPMethodView):

    async def get(self, request):
        return text('hello momo!')


class KWResponse(HTTPMethodView):

    async def get(self, request):
        args = request.raw_args
        uid = args.get('uid')
        word = args.get('word')
        kwr = KWR(uid, word)
        value = kwr.get_response()
        return text(value or 'please input')


class Tags(HTTPMethodView):

    def get(self, request):
        args = request.raw_args
        _tag = args.get('tag')
        tag = Tag.insert(name=_tag, created_time=datetime.utcnow())
        return text(_tag)


class ChatBot(HTTPMethodView):

    async def get(self, request):
        ask = request.args.get('ask')
        if ask:
            answer = get_momo_answer(ask)
            return text(answer)
        return text('你说啥?')


blueprint.add_route(Index.as_view(), '/')
# blueprint.add_route(Tags.as_view(), '/add_tag')
# blueprint.add_route(ChatBot.as_view(), '/momo')
# blueprint.add_route(KWResponse.as_view(), '/kwr')
