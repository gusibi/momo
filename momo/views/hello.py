# -*- coding: utf-8 -*-

from sanic import Sanic, Blueprint
from sanic.views import HTTPMethodView
from sanic.response import text

from momo.helper import get_momo_answer


blueprint = Blueprint('index', url_prefix='/')


class Index(HTTPMethodView):

    async def get(self, request):
        return text('hello momo!')



class ChatBot(HTTPMethodView):

    async def get(self, request):
        ask = request.args.get('ask')
        if ask:
            answer = get_momo_answer(ask)
            return text(answer)
        return text('你说啥?')


blueprint.add_route(Index.as_view(), '/')
blueprint.add_route(ChatBot.as_view(), '/momo')
