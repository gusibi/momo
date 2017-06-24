# -*- coding: utf-8 -*-

from sanic import Sanic, Blueprint
from sanic.views import HTTPMethodView
from sanic.response import text


blueprint = Blueprint('index', url_prefix='/')


class Index(HTTPMethodView):

    async def get(self, request):
        return text('hello momo!')


blueprint.add_route(Index.as_view(), '/')