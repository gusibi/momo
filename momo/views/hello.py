# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import current_app as app, views, Blueprint

blueprint = Blueprint('index', __name__)


class Hello(views.MethodView):

    def get(self):
        return 'hello momo!'


blueprint.add_url_rule('/hello', endpoint='request',
                       view_func=Hello.as_view('request'))
