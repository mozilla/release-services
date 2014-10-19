# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import time

from flask import url_for

from copy import deepcopy
from nose.tools import assert_greater
from nose.tools import eq_

from relengapi.lib.testing.context import TestContext

from models import Build
from models import ClobberTime
from models import DB_DECLARATIVE_BASE

_clobber_args = {
    'branch': 'branch',
    'builddir': 'builddir',
}

test_context = TestContext(databases=[DB_DECLARATIVE_BASE], reuse_app=True)

_last_clobber_args = deepcopy(_clobber_args)
_last_clobber_args['buildername'] = 'buildername'


@test_context
def test_clobber_request(client):
    with client.application.test_request_context():
        session = test_context._app.db.session(DB_DECLARATIVE_BASE)
        clobber_count_initial = session.query(ClobberTime).count()
        rv = client.post_json(url_for('clobberer.clobber'), data=[_clobber_args])
        eq_(rv.status_code, 200)
        clobber_count_final = session.query(ClobberTime).count()

        eq_(clobber_count_final, clobber_count_initial + 1,
            'No new clobbers were detected, clobber request failed.')


@test_context
def test_lastclobber(client):
    with client.application.test_request_context():
        session = test_context._app.db.session(DB_DECLARATIVE_BASE)
        rv = client.get(
            '{}?branch={branch}&builddir={builddir}&buildername={buildername}'.format(
                url_for('clobberer.lastclobber'), **_last_clobber_args
            )
        )
        eq_(rv.status_code, 200)
        lastclobber_data = rv.data.strip().split(':')
        eq_(lastclobber_data[0], _last_clobber_args['builddir'])
        eq_(lastclobber_data[1].isdigit(), True,
            'lastclobber did not return a valid timestamp => {}'.format(lastclobber_data[1]))
        eq_(lastclobber_data[2], 'anonymous',
            'lastclobber did not return a valid username')

        # Ensure a new build has been recorded matching the request args
        for k, v in _last_clobber_args.items():
            build = session.query(Build).first()
            eq_(getattr(build, k), v)

        # Ensure that a request for non-existant data returns nothing gracefully
        rv = client.get('{}?branch=fake&builddir=bogus'.format(
                url_for('clobberer.lastclobber')
            )
        )
        eq_(rv.status_code, 200)
        eq_(rv.data, "")


@test_context
def test_branches(client):
    with client.application.test_request_context():
        rv = client.get(url_for('clobberer.branches'))
    eq_(rv.status_code, 200)
    eq_(json.loads(rv.data)["result"], ['branch', 'fake'])


@test_context
def test_lastclobber_by_builder(client):
    with client.application.test_request_context():
        rv = client.get(url_for('clobberer.lastclobber_by_builder', branch='branch'))
    eq_(rv.status_code, 200)
    buildername = _last_clobber_args.get("buildername")
    clobbertimes = json.loads(rv.data)["result"]
    eq_(type(clobbertimes.get(buildername)), list)
    eq_(len(clobbertimes.get(buildername)), 1)
    # Make sure all of our clobber fields were retrieved
    for key, value in _clobber_args.items():
        eq_(clobbertimes.get(buildername)[0].get(key), value)

@test_context
def test_forceclobber(client):
    with client.application.test_request_context():
        rv = client.get('{}?builddir=lamesauce'.format(url_for('clobberer.forceclobber')))
    eq_(rv.status_code, 200)
    builddir, future_time, who = rv.data.split('\n')[0].split(':')
    eq_(builddir, 'lamesauce')
    assert_greater(int(future_time), int(time.time()))
