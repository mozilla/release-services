# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import threading

from nose.tools import eq_
from nose.tools import with_setup
from relengapi.lib.proxy import proxy
from relengapi.lib.testing.context import TestContext

try:
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
except ImportError:
    from http.server import HTTPServer, BaseHTTPRequestHandler


class ProxiedRequest(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('content-type', 'text/plain')
        self.end_headers()
        self.wfile.write("proxied")

    def log_request(self, code=None, size=None):
        return


class ProxyTarget(HTTPServer):

    def __init__(self, address, request_class):
        self.port_set = threading.Event()
        self.port_set = threading.Event()
        HTTPServer.__init__(self, address, request_class)

    def server_bind(self):
        HTTPServer.server_bind(self)
        self.port_set.set()

server_thread = None


def start_server():
    global server_thread
    server = ProxyTarget(('', 0), ProxiedRequest)
    server_thread = threading.Thread(target=server.handle_request)
    server_thread.start()
    # wait until it picks a port
    server.port_set.wait()
    return server.server_port


def stop_server():
    server_thread.join(1)
    assert not server_thread.isAlive(), "thread didn't complete"


@TestContext()
@with_setup(teardown=stop_server)
def test_proxy(app, client):
    # setup a backend server
    port = start_server()
    # add a route to proxy to the backend

    @app.route('/proxytest')
    def proxytest():
        return proxy('http://127.0.0.1:%d' % port)
    # get the frontend
    rv = client.get('/proxytest')
    # check the result
    eq_(rv.data, 'proxied')
