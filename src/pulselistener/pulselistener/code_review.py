# -*- coding: utf-8 -*-
import asyncio
import time

import hglib
from libmozdata.phabricator import UnitResult
from libmozdata.phabricator import UnitResultState

from cli_common.log import get_logger
from cli_common.pulse import run_consumer
from pulselistener.lib.bus import MessageBus
from pulselistener.lib.mercurial import Repository
from pulselistener.lib.phabricator import Phabricator
from pulselistener.lib.phabricator import PhabricatorBuild
from pulselistener.lib.phabricator import PhabricatorBuildState
from pulselistener.lib.web import WebServer

logger = get_logger(__name__)

TREEHERDER_URL = 'https://treeherder.mozilla.org/#/jobs?repo={}&revision={}'


class CodeReview(object):
    '''
    Code Review events workflow
    '''
    QUEUE_BUILDS = 'builds'

    def __init__(self, config, cache_root, taskcluster_client_id=None, taskcluster_access_token=None):
        # Setup webserver
        self.webserver = WebServer()

        # Start phabricator
        self.phabricator_publish = config.get('phabricator_publish', False)
        logger.info('Phabricator publication is {}'.format(self.phabricator_publish and 'enabled' or 'disabled'))  # noqa

        self.phabricator = Phabricator(
            api_key=config['PHABRICATOR']['token'],
            url=config['PHABRICATOR']['url'],
            retries=config.get('phabricator_retries', 5),
            sleep=config.get('phabricator_sleep', 10),
        )

        # Configure repositories, and index them by phid
        self.repositories = {
            phab_repo['phid']: Repository(conf, cache_root)
            for phab_repo in self.phabricator.api.list_repositories()
            for conf in config['repositories']
            if phab_repo['fields']['name'] == conf['name']
        }
        assert len(self.repositories) > 0, 'No repositories configured'
        logger.info('Configured repositories', names=[r.name for r in self.repositories.values()])

        # Setup communication bus
        self.bus = MessageBus()
        self.bus.add_queue(CodeReview.QUEUE_BUILDS)
        self.webserver.register(self.bus)
        self.phabricator.register(self.bus)

    def run(self):
        # Webserver runs in a dedicated process
        # Needs to run ASAP to meet Heroku boot requirements
        self.webserver.start()

        # First clone all repositories
        for repo in self.repositories.values():
            repo.clone()

        # Then process events
        logger.info('Running code review events...')
        tasks = [
            # When a build is received on the web server
            # check its visibility on phabricator
            self.load_builds(),

            # Apply new builds on local repositories
            # and send reporting informations to Phabricator
            self.bus.run(CodeReview.QUEUE_BUILDS, Phabricator.QUEUE_PUBLISH, self.apply_build),
        ]

        # Add publication tasks only when Phabricator reporting is enabled
        if self.phabricator_publish is True:
            tasks.append(self.phabricator.publish())

        run_consumer(asyncio.gather(*tasks))

    async def load_builds(self):
        '''
        Workflow to check Phabricator build's visibility
        then loading their extended informations (patches & commits)
        '''
        while self.bus.is_alive():
            build = await self.bus.receive(WebServer.QUEUE_OUT)
            assert isinstance(build, PhabricatorBuild)

            # Check visibility of builds in queue
            # The build state is updated to public/secured there
            if build.state == PhabricatorBuildState.Queued:
                self.phabricator.check_visibility(build)

            if build.state == PhabricatorBuildState.Public:
                # Enqueue push to try
                await self.bus.send(CodeReview.QUEUE_BUILDS, build)

                # Report public bug as working
                await self.bus.send(Phabricator.QUEUE_PUBLISH, ('working', build))

            elif build.state == PhabricatorBuildState.Secured:
                # We cannot send any update on a Secured build
                # as the bot has no edit access on it
                logger.info('Secured revision, skipping.', build=build.target_phid)

            else:
                # By default requeue build until it's marked secured or public
                await self.bus.send(WebServer.QUEUE_OUT, build)

            await asyncio.sleep(0)

    async def apply_build(self, build):
        '''
        Try to load and apply a diff on local clone
        If successful, push to try and build a treeherder link
        If failure, build a unit result with a warning message
        '''
        assert isinstance(build, PhabricatorBuild)
        assert build.target_phid is not None

        # Select repository
        repository = self.repositories.get(build.repo_phid)
        assert repository is not None, 'Missing repository for build {}'.format(build)

        start = time.time()
        try:
            # Start by cleaning the repo
            repository.clean()

            # First apply patches on local repo
            await repository.apply_patches(build.stack)

            # Configure the try task
            repository.add_try_commit(build)

            # Then push that stack on try
            tip = repository.push_to_try()
            logger.info('Diff has been pushed !')
        except hglib.error.CommandError as e:
            # Format nicely the error log
            error_log = e.err
            if isinstance(error_log, bytes):
                error_log = error_log.decode('utf-8')

            logger.warn('Mercurial error on diff', error=error_log, args=e.args, build=build)

            # Report mercurial failure as a Unit Test issue
            failure = UnitResult(
                namespace='code-review',
                name='mercurial',
                result=UnitResultState.Fail,
                details='WARNING: The code review bot failed to apply your patch.\n\n```{}```'.format(error_log),
                format='remarkup',
                duration=time.time() - start,
            )
            return ('failure', build, failure)

        except Exception as e:
            logger.warn('Failed to process diff', error=e, build=build)

            # Report generic failure as a Unit Test issue
            failure = UnitResult(
                namespace='code-review',
                name='general',
                result=UnitResultState.Broken,
                details='WARNING: An error occured in the code review bot.\n\n```{}```'.format(e),
                format='remarkup',
                duration=time.time() - start,
            )
            return ('failure', build, failure)

        # Publish Treeherder link
        uri = TREEHERDER_URL.format(repository.try_name, tip.node.decode('utf-8'))
        return ('treeherder_link', build, uri)
