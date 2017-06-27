# -*- coding: utf-8 -*-

from sanic import Sanic, Blueprint
from sanic.views import HTTPMethodView
from sanic.response import text

from momo.models.wx_response import KWResponse as KWR


blueprint = Blueprint('index', url_prefix='/')


class Index(HTTPMethodView):

    async def get(self, request):
        return text('hello momo!')


class KWResponse(HTTPMethodView):

    async def get(self, request):
        args = request.raw_args
        word = args.get('word')
        kwr = KWR('gs', word)
        value = kwr.get_response()
        return text(value or 'please input')



blueprint.add_route(Index.as_view(), '/')
blueprint.add_route(KWResponse.as_view(), '/kwr')
