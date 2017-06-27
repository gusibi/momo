# -*- coding: utf-8 -*-
import asyncio

import uvloop
from sanic import Sanic

from momo.settings import Config


blueprints = []


def create_app(register_bp=True, test=False):
    app = Sanic(__name__)
    if test:
        app.config['TESTING'] = True
    app.config.from_object(Config)
    register_blueprints(app)
    return app


def register_extensions(app):
    pass


def register_blueprints(app):
    from momo.views.hello import blueprint as hello_bp
    from momo.views.mweixin import blueprint as wx_bp
    app.register_blueprint(hello_bp)
    app.register_blueprint(wx_bp)


def register_jinja_funcs(app):
    # funcs = dict()
    return app

app = create_app()
asyncio.set_event_loop(uvloop.new_event_loop())
server = app.create_server(host="0.0.0.0", port=8000, debug=True)
loop = asyncio.get_event_loop()
task = asyncio.ensure_future(server)
try:
    loop.run_forever()
except:
    loop.stop()
