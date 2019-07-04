# -*- coding: utf-8 -*-
import pytest

from pulselistener.listener import HookPhabricator
from pulselistener.phabricator import PhabricatorBuild


class MockURL():
    def __init__(self, **kwargs):
        self.query = kwargs


class MockRequest():
    def __init__(self, **kwargs):
        self.rel_url = MockURL(**kwargs)


@pytest.mark.asyncio
async def test_risk_analysis_should_trigger(PhabricatorMock):
    with PhabricatorMock as api:
        phabricator = HookPhabricator({
          'hookId': 'services-staging-staticanalysis/bot',
          'mode': 'webhook',
          'actions': ['try'],
          'phabricator_retries': 3,
          'phabricator_sleep': 4,
          'risk_analysis_reviewers': ['ehsan', 'heycam'],
          'phabricator_api': api,
        })

        build = PhabricatorBuild(MockRequest(
            diff='125397',
            repo='PHID-REPO-saax4qdxlbbhahhp2kg5',
            revision='36474',
            target='PHID-HMBT-icusvlfibcebizyd33op'
        ))
        build.check_visibility(api, phabricator.secure_projects, phabricator.phabricator_retries, phabricator.phabricator_sleep)

        assert phabricator.should_run_risk_analysis(build)


@pytest.mark.asyncio
async def test_risk_analysis_shouldnt_trigger(PhabricatorMock):
    with PhabricatorMock as api:
        phabricator = HookPhabricator({
          'hookId': 'services-staging-staticanalysis/bot',
          'mode': 'webhook',
          'actions': ['try'],
          'phabricator_retries': 3,
          'phabricator_sleep': 4,
          'risk_analysis_reviewers': ['ehsan'],
          'phabricator_api': api,
        })

        build = PhabricatorBuild(MockRequest(
            diff='125397',
            repo='PHID-REPO-saax4qdxlbbhahhp2kg5',
            revision='36474',
            target='PHID-HMBT-icusvlfibcebizyd33op'
        ))
        build.check_visibility(api, phabricator.secure_projects, phabricator.phabricator_retries, phabricator.phabricator_sleep)

        assert not phabricator.should_run_risk_analysis(build)
