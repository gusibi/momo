# -*- coding: utf-8 -*-
# from gevent.monkey import patch_all; patch_all()

import re
import os
import yaml
import time
import os.path
import tempfile
from werkzeug.serving import BaseRequestHandler
from flask_script import Manager, Server
from six.moves.urllib.parse import unquote

from momo.helper import smart_str

# update zaih.app to your appname
from momo.app import create_app

app = create_app()
manager = Manager(app)

staticPattern = app.config.get(
    'COLOR_PATTERN_GRAY',
    r'^/(static|assets|img|js|css)/(.*)|favicon\.ico|(.*)\.(png|jpeg|jpg|gif|css)$')
hidePattern = app.config.get('COLOR_PATTERN_HIDE', r'/^$/')


class RequestHandler(BaseRequestHandler):
    """Extend werkzeug request handler to suit our needs."""

    RED = '\033[31m'
    GREEN = '\033[32m'
    LIGHTGREEN = '\033[92m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    HEADER = '\033[35m'
    GRAY = '\033[90m'
    LITTLEGRAY = '\033[37m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'

    def handle(self):
        self.Started = time.time()
        rv = super(RequestHandler, self).handle()
        return rv

    def send_response(self, *args, **kw):
        self.Processed = time.time()
        super(RequestHandler, self).send_response(*args, **kw)

    def log_request(self, code='-', size='-'):
        requestline = self.requestline
        method, url, httpv = requestline.split(" ")
        url = smart_str(unquote(url))

        if code == 200:
            statusColor = self.GREEN
        elif str(code)[0] in ['4', '5']:
            statusColor = self.RED
        else:
            statusColor = self.LITTLEGRAY

        if method == 'GET':
            methodColor = self.BLUE
        elif method in ['POST', 'PUT']:
            methodColor = self.LIGHTGREEN
        else:
            methodColor = self.RED

        if re.search(hidePattern, url):
            return

        duration = int((self.Processed - self.Started) * 1000)

        message = '{methodColor}{method}{colorEnd} {urlColor}{url}{colorEnd} {httpv} {statusColor}{status}{colorEnd} {size} {durationColor}[{duration}ms]{colorEnd}'.format(
                         url=url, size=size, status=code, httpv=httpv,
                         method=method, duration=duration,
                         urlColor=self.HEADER,
                         statusColor=statusColor,
                         methodColor=methodColor,
                         durationColor=self.CYAN,
                         colorEnd=self.ENDC)
        message = smart_str(unquote(message))
        self.log('info', message)


@manager.command
def test():
    """Run the tests."""
    import subprocess
    code = subprocess.call(['py.test', 'tests', '--cov',
                            'zaih-ed', '--verbose'])
    return code


@manager.command
def fixture():
    pass


def dirfile(path):
    tmpfile = tempfile.NamedTemporaryFile(delete=False)
    for roots, dirs, files in os.walk(path):
        yml_files = [f for f in files if f.endswith('.yml')]
        for fn in yml_files:
            fn = '/'.join([path, fn])
            with open(fn, 'r') as f:
                tmpfile.write(f.read())
    tmpfile.seek(0)
    tmpfile.close()
    return tmpfile.name


class Loader(yaml.Loader):

    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]
        super(Loader, self).__init__(stream)

    def include(self, node):
        is_delete = False
        filename = os.path.join(self._root, self.construct_scalar(node))
        if os.path.isdir(filename):
            print(filename)
            filename = dirfile(filename)
            print(filename)
            is_delete = True
        with open(filename, 'r') as f:
            return yaml.load(f, Loader)
        if is_delete and os.path.exists(filename):
            os.unlink(filename)

Loader.add_constructor('!include', Loader.include)


@manager.option('-s', '--source', help='source file for convert', default='docs/base.yml')
@manager.option('-d', '--dist', help='file name that you will save', default='docs/v1.yml')
def swagger_merge(source, dist):
    with open(source, 'r') as f:
        data = yaml.load(f, Loader)
    with open(dist, 'w') as f:
        f.write(yaml.dump(data))
    print('merge success!')


# swagger_py_codegen -s  docs/apis.yml  apis_src -p zhinsta
@manager.option('-s', '--swagger', help='Swagger doc file.', default='docs/v1.yml')
@manager.option('-p', '--package', help='Package name / application name', default='momo')
@manager.option('-d', '--dist', help='Package name / application name', default='.')
def swagger_py_codegen(swagger, dist, package):
    if dist:
        command = 'swagger_py_codegen -s %s %s -p %s --ui --spec' % (swagger, dist, package)
    else:
        command = 'swagger_py_codegen -s %s -p %s --ui --spec' % (swagger, package)
    print(command)
    os.system(command)
    # copy genarate code to momo
    print('code generate success!')


manager.add_command('server', Server(host='0.0.0.0', port='8888',
                                     use_reloader=True, threaded=True,
                                     request_handler=RequestHandler))


if __name__ == '__main__':
    manager.run()
