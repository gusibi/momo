# -*- coding: utf-8 -*-
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
    return app
