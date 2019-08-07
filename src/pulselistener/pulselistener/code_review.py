# -*- coding: utf-8 -*-
import structlog
from libmozdata.phabricator import BuildState
from libmozdata.phabricator import UnitResult
from libmozdata.phabricator import UnitResultState

from pulselistener.lib.mercurial import Repository
from pulselistener.lib.phabricator import PhabricatorActions
from pulselistener.lib.phabricator import PhabricatorBuild
from pulselistener.lib.phabricator import PhabricatorBuildState

logger = structlog.get_logger(__name__)


class PhabricatorCodeReview(PhabricatorActions):
    '''
    Actions related to Phabricator for the code review events
    '''
    def __init__(self, publish=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.publish = publish
        logger.info('Phabricator publication is {}'.format(self.publish and 'enabled' or 'disabled'))

    def register(self, bus):
        self.bus = bus

    def get_repositories(self, repositories, cache_root):
        '''
        Configure repositories, and index them by phid
        '''
        repositories = {
            phab_repo['phid']: Repository(conf, cache_root)
            for phab_repo in self.api.list_repositories()
            for conf in repositories
            if phab_repo['fields']['name'] == conf['name']
        }
        assert len(repositories) > 0, 'No repositories configured'
        logger.info('Configured repositories', names=[r.name for r in repositories.values()])
        return repositories

    async def load_builds(self, input_name, output_name):
        '''
        Code review workflow to load all necessary information from Phabricator builds
        received from the webserver
        '''
        while True:

            # Receive build from webserver
            build = await self.bus.receive(input_name)
            assert isinstance(build, PhabricatorBuild)

            # Update its state
            self.update_state(build)

            if build.state == PhabricatorBuildState.Public:
                # When the build is public, load needed details
                try:
                    self.load_patches_stack(build)
                    logger.info('Loaded stack of patches', build=str(build))

                    self.load_reviewers(build)
                    logger.info('Loaded reviewers', build=str(build))
                except Exception as e:
                    logger.warning('Failed to load build details', build=str(build), error=str(e))
                    continue

                # Then send the build toward next stage
                await self.bus.send(output_name, build)

            elif build.state == PhabricatorBuildState.Queued:
                # Requeue when nothing changed for now
                await self.bus.send(input_name, build)

    def publish_results(self, payload):
        assert self.publish is True, 'Publication disabled'
        mode, build, extras = payload
        logger.debug('Publishing a Phabricator build update', mode=mode, build=build)

        if mode == 'fail:general':
            failure = UnitResult(
                namespace='code-review',
                name='general',
                result=UnitResultState.Broken,
                details='WARNING: An error occured in the code review bot.\n\n```{}```'.format(extras['message']),
                format='remarkup',
                duration=extras.get('duration', 0)
            )
            self.api.update_build_target(build.target_phid, BuildState.Fail, unit=[failure])

        elif mode == 'fail:mercurial':
            failure = UnitResult(
                namespace='code-review',
                name='mercurial',
                result=UnitResultState.Fail,
                details='WARNING: The code review bot failed to apply your patch.\n\n```{}```'.format(extras['message']),
                format='remarkup',
                duration=extras.get('duration', 0)
            )
            self.api.update_build_target(build.target_phid, BuildState.Fail, unit=[failure])

        elif mode == 'success':
            self.api.create_harbormaster_uri(build.target_phid, 'treeherder', 'Treeherder Jobs', extras['treeherder_url'])

        elif mode == 'work':
            self.api.update_build_target(build.target_phid, BuildState.Work)
            logger.info('Published public build as working', build=str(build))

        else:
            logger.warning('Unsupported publication', mode=mode, build=build)

        return True
