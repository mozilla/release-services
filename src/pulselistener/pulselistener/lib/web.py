# -*- coding: utf-8 -*-
import os
from multiprocessing import Process

import structlog
from aiohttp import web

from pulselistener.lib.phabricator import PhabricatorBuild

logger = structlog.get_logger(__name__)


class WebServer(object):
    '''
    WebServer used to receive hook
    '''
    def __init__(self, queue_name):
        self.process = None
        self.http_port = int(os.environ.get('PORT', 9000))
        self.queue_name = queue_name
        logger.info('HTTP webhook server will listen', port=self.http_port)

        # Configure the web application with code review routes
        self.app = web.Application()
        self.app.add_routes([
            web.get('/ping', self.ping),
            web.post('/codereview/new', self.create_code_review),
        ])

    def register(self, bus):
        self.bus = bus
        self.bus.add_queue(self.queue_name, mp=True, redis=True)

    def start(self):
        '''
        Run the web server used by hooks in its own process
        '''
        def _run():
            web.run_app(self.app, port=self.http_port, print=logger.info)

        # Run webserver in its own process
        self.process = Process(target=_run)
        self.process.start()
        logger.info('Web server started', pid=self.process.pid)

        return self.process

    def stop(self):
        assert self.process is not None, 'Web server not started'
        self.process.kill()
        logger.info('Web server stopped')

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
            await self.bus.send(self.queue_name, build)
        except Exception as e:
            logger.error(str(e), path=request.path_qs)
            raise web.HTTPBadRequest(text=str(e))

        logger.info('Queued new build', build=str(build))
        return web.Response(text='Build queued')
