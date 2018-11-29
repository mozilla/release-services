# -*- coding: utf-8 -*-
# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import responses


@responses.activate
def test_libmozdata():
    '''
    Test libmozdata to use custom user agent specified in mozdata.ini
    '''
    from uplift_bot.bugzilla import use_bugzilla, Bugzilla
    use_bugzilla('https://bugzilla')
    responses.add(responses.GET, 'https://bugzilla/rest/bug?id=1', json={'bugs': [{'id': 1, 'name': 'bug 1'}]}, status=200)

    def _bughandler(bug, data):
        bugid = bug['id']
        data[bugid] = bug

    bugs = {}

    bz = Bugzilla(bugids=['1'], include_fields=[], bughandler=_bughandler, bugdata=bugs)
    bz.get_data().wait()

    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == 'https://bugzilla/rest/bug?id=1'
    assert responses.calls[0].request.headers['User-Agent'] == 'uplift-bot'

    assert len(bugs) == 1
    assert bugs == {1: {'id': 1, 'name': 'bug 1'}}
