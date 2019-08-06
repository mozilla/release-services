# -*- coding: utf-8 -*-

import pytest

from pulselistener.lib.bus import MessageBus
from pulselistener.lib.phabricator import PhabricatorBuild
from pulselistener.listener import HookPhabricator


class MockURL():
    def __init__(self, **kwargs):
        self.query = kwargs


class MockRequest():
    def __init__(self, **kwargs):
        self.rel_url = MockURL(**kwargs)


@pytest.mark.asyncio
async def test_risk_analysis_should_trigger(PhabricatorMock, mock_taskcluster):
    bus = MessageBus()

    client = HookPhabricator({
      'hookId': 'services-staging-staticanalysis/bot',
      'mode': 'webhook',
      'actions': ['try'],
      'risk_analysis_reviewers': ['ehsan', 'heycam'],
    }, bus)

    build = PhabricatorBuild(MockRequest(
        diff='125397',
        repo='PHID-REPO-saax4qdxlbbhahhp2kg5',
        revision='36474',
        target='PHID-HMBT-icusvlfibcebizyd33op'
    ))

    # Load reviewers using mock
    with PhabricatorMock as phab:
        phab.update_state(build)
        phab.load_reviewers(build)

    assert client.should_run_risk_analysis(build)


@pytest.mark.asyncio
async def test_risk_analysis_shouldnt_trigger(PhabricatorMock, mock_taskcluster):
    bus = MessageBus()
    client = HookPhabricator({
      'hookId': 'services-staging-staticanalysis/bot',
      'mode': 'webhook',
      'actions': ['try'],
      'risk_analysis_reviewers': ['ehsan'],
    }, bus)

    build = PhabricatorBuild(MockRequest(
        diff='125397',
        repo='PHID-REPO-saax4qdxlbbhahhp2kg5',
        revision='36474',
        target='PHID-HMBT-icusvlfibcebizyd33op'
    ))

    # Load reviewers using mock
    with PhabricatorMock as phab:
        phab.update_state(build)
        phab.load_reviewers(build)

    assert not client.should_run_risk_analysis(build)
