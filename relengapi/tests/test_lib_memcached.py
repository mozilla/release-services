# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import contextlib
import itertools
import mock
import socket

from nose.tools import eq_
from relengapi.lib.testing.context import TestContext

test_context = TestContext(reuse_app=False)


def ne_(a, b):
    assert a != b, "%r == %r" % (a, b)


@contextlib.contextmanager
def mock_auto_discovery(return_values):
    def replacement(config, time_to_timeout=None):
        rv = return_values.pop(0)
        if isinstance(rv, socket.error):
            raise rv
        return rv

    p = mock.patch('elasticache_auto_discovery.discover',
                   autospec=True, side_effect=replacement)
    p.start()
    try:
        yield
    finally:
        p.stop()
        # ensure we used all of the values
        eq_(return_values, [])


@test_context
def test_mock(app):
    with app.memcached.cache('mock://tests') as mc:
        mc.set('x', '20')
        eq_(mc.get('x'), '20')
    # ensure the value sticks around
    with app.memcached.cache('mock://tests') as mc:
        eq_(mc.get('x'), '20')


@test_context
def test_direct(app):
    fakeClients = itertools.count(1)

    def fakeClient(config):
        return (config[0], fakeClients.next())

    with mock.patch('memcache.Client', autospec=True,
                    side_effect=fakeClient) as Client:
        # simulate three overlapping calls, for two configs
        with app.memcached.cache(['1.1.1.1']) as mc1a:
            with app.memcached.cache(['2.2.2.2']) as mc2a:
                with app.memcached.cache(['1.1.1.1']) as mc1b:
                    pass
        # get mc1a and mc1b again, just to confirm
        with app.memcached.cache(['1.1.1.1']) as mc1a2:
            with app.memcached.cache(['1.1.1.1']) as mc1b2:
                pass

        eq_(Client.mock_calls, [
            mock.call(['1.1.1.1']),
            mock.call(['2.2.2.2']),
            mock.call(['1.1.1.1']),
        ])

        ne_(mc1a, mc2a)

        # note that this is an implementation detail: these could easily
        # be reversed
        eq_(mc1a, mc1a2)
        eq_(mc1b, mc1b2)


@test_context
def test_elasticache(app):
    response = [['host1', '1.1.1.1', '11211'], ['host2', '2.2.2.2', '11211']]
    with mock.patch('memcache.Client', autospec=True) as Client, \
            mock_auto_discovery([response]), \
            app.memcached.cache('elasticache://9.9.9.9:9'):
        pass

    Client.assert_called_with(['1.1.1.1:11211', '2.2.2.2:11211'])


@test_context
def test_elasticache_polling(app):
    response1 = [['host1', '1.1.1.1', '11211'], ['host2', '2.2.2.2', '11211']]
    response2 = [['host3', '3.3.3.3', '11211'], ['host2', '2.2.2.2', '11211']]
    with mock.patch('time.time', autospec=True) as time, \
            mock.patch('memcache.Client', autospec=True) as Client, \
            mock_auto_discovery([response1, response2]):
        time.return_value = 1000
        with app.memcached.cache('elasticache://9.9.9.9') as mc1:
            eq_(Client.mock_calls, [
                mock.call(['1.1.1.1:11211', '2.2.2.2:11211'])])
            Client.reset_mock()
        time.return_value = 2000
        with app.memcached.cache('elasticache://9.9.9.9') as mc2:
            # no new client
            assert mc1 is mc2
            # but reconfigured
            eq_(Client.mock_calls, [
                mock.call().set_servers(['3.3.3.3:11211', '2.2.2.2:11211'])])


@test_context
def test_elasticache_socket_error_keep(app):
    response = [['host1', '1.1.1.1', '11211'], ['host2', '2.2.2.2', '11211']]
    with mock.patch('time.time', autospec=True) as time, \
            mock.patch('memcache.Client', autospec=True) as Client, \
            mock_auto_discovery([response, socket.error(1234)]):
        time.return_value = 1000
        with app.memcached.cache('elasticache://9.9.9.9') as mc1:
            eq_(Client.mock_calls, [
                mock.call(['1.1.1.1:11211', '2.2.2.2:11211'])])
            Client.reset_mock()
        time.return_value = 2000
        with app.memcached.cache('elasticache://9.9.9.9') as mc2:
            # no new client
            assert mc1 is mc2
            # reconfigured, but with the old config
            eq_(Client.mock_calls, [
                mock.call().set_servers(['1.1.1.1:11211', '2.2.2.2:11211'])])


@test_context
def test_elasticache_socket_error_fallback(app):
    with mock.patch('memcache.Client', autospec=True) as Client:
        with app.memcached.cache('elasticache://127.0.0.1:0'):
            eq_(Client.mock_calls, [
                # the fallback server
                mock.call(['127.0.0.1:11211'])])
