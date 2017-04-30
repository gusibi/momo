# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import Flask
from werkzeug.utils import import_string

from momo.settings import Config


blueprints = [
    'momo.views.mweixin:blueprint',
    'momo.views.hello:blueprint',
]


def create_app(register_bp=True, test=False):
    app = Flask(__name__, static_folder='static')
    if test:
        app.config['TESTING'] = True
    app.config.from_object(Config)
    register_extensions(app)
    register_before_request(app)
    register_after_request(app)
    if register_bp:
        register_blueprints(app)
    return app


def register_extensions(app):
    pass


def register_blueprints(app):
    for bp in blueprints:
        app.register_blueprint(import_string(bp))


def register_jinja_funcs(app):
    funcs = dict(
    )
    app.jinja_env.globals.update(funcs)
    return app


def register_after_request(app):

    def print_error_content(response):
        if response.status not in [200, 201, 204]:
            print(response.data)
            return response
    app.after_request(print_error_content)


def register_before_request(app):
    def get_request_ip():
        from flask import g, request
        g.ip = request.headers.get('x-forwarded-for') or request.remote_addr

    app.before_request(get_request_ip)
