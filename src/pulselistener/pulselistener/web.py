# -*- coding: utf-8 -*-
import os
from multiprocessing import Process
from multiprocessing import Queue

from aiohttp import web

from cli_common.log import get_logger
from pulselistener.phabricator import PhabricatorBuild

logger = get_logger(__name__)


class WebServer(object):
    '''
    WebServer used to receive hook
    '''

    def __init__(self):
        self.http_port = int(os.environ.get('PORT', 9000))
        logger.info('HTTP webhook server will listen', port=self.http_port)

        self.queue = Queue()

        # Configure the web application with routes
        self.app = web.Application()
        self.app.add_routes([
            web.get('/ping', self.ping),
            web.post('/codereview/new', self.create_code_review),
        ])

    def start(self):
        '''
        Run the web server used by hooks in its own process
        '''
        def _run():
            web.run_app(self.app, port=self.http_port, print=logger.info)

        # Run webserver in its own process
        server = Process(target=_run)
        server.start()
        logger.info('Web server started', pid=server.pid)

        return server

    async def ping(self, request):
        '''
        Dummy test endpoint
        '''
        return web.Response(text='pong')

    async def create_code_review(self, request):
        '''
        HTTP POST webhook used by HarborMaster on new builds
        It only stores build ids and reply ASAP
        Mandatory query parameters:
        * diff as ID
        * repo as PHID
        * revision as ID
        * target as PHID
        '''
        try:
            build = PhabricatorBuild(request)
            self.queue.put(build)
        except Exception as e:
            logger.error(str(e), path=request.path_qs)
            raise web.HTTPBadRequest(text=str(e))

        logger.info('Queued new build', build=build)
        return web.Response(text='Build queued')
