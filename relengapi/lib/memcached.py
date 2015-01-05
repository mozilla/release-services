# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import contextlib
import elasticache_auto_discovery
import logging
import memcache
import socket
import threading
import time
import urlparse

logger = logging.getLogger(__name__)


class BaseCacheFinder(object):

    def __init__(self):
        self.lock = threading.Lock()
        self._values = {}  # format is up to the subclass

    def acquire_cache(self, config):
        '''Lock and return a cache client with the given config.  Returns a
        cache and a "cookie" which can later be used to release the cache.'''

    def release_cache(self, cookie):
        '''Release the cache client with the given cookie'''

    def _value_for_config(self, config):
        '''Make a new value for self._get; called with the finder lock
        held.'''

    def _get(self, name, config=None):
        '''Get, making if necessary, a new value for the given name and
        configuration.  If `config` is omitted, then the value must already
        exist.'''
        with self.lock:
            try:
                return self._values[name]
            except KeyError:
                assert config is not None
                rv = self._values[name] = self._value_for_config(config)
                return rv


class MockCacheFinder(BaseCacheFinder):

    def _value_for_config(self, config):
        import mockcache
        return mockcache.Client(), threading.Lock()

    def acquire_cache(self, config):
        mc, lock = self._get(config, config)
        # wait forever for the cache to become available, since the data is all
        # stored inside it.
        lock.acquire()
        return mc, config

    def release_cache(self, cookie):
        _, lock = self._get(cookie)
        lock.release()


class MemcachedCacheFinder(BaseCacheFinder):

    def _value_for_config(self, config):
        # an empty list of wrappers; acquire_cache will add wrappers to
        # this list as necessary
        return []

    def acquire_cache(self, config):
        name = str(config)
        wrappers = self._get(name, config)
        # find an unlocked cache (again under the finder lock)
        with self.lock:
            for i in xrange(len(wrappers)):
                if wrappers[i].lock.acquire(False):
                    cookie = name, i
                    return wrappers[i].checkout(), cookie
            # or make a new one (note that these are never collected)
            else:
                cookie = name, len(wrappers)
                wrapper = self.client_wrapper_class(config)
                wrappers.append(wrapper)
                wrapper.lock.acquire()
                return wrapper.checkout(), cookie

    def release_cache(self, cookie):
        name, i = cookie
        wrappers = self._get(name)
        wrappers[i].lock.release()


class ClientWrapper(object):

    def __init__(self, config):
        self.lock = threading.Lock()

    def checkout(self):
        '''Get the actual memcached.Client object'''


class DirectCacheClientWrapper(ClientWrapper):

    def __init__(self, config):
        super(DirectCacheClientWrapper, self).__init__(config)
        self.client = memcache.Client(config)

    def checkout(self):
        return self.client


class DirectCacheFinder(MemcachedCacheFinder):

    client_wrapper_class = DirectCacheClientWrapper


class ElastiCacheClientWrapper(ClientWrapper):

    POLL_INTERVAL = 600  # check for config updates every ten minutes

    def __init__(self, config):
        super(ElastiCacheClientWrapper, self).__init__(config)
        self.elasticache_config = config
        self.last_memcache_config = None
        self.last_poll = time.time()
        memcache_config = self.get_memcache_config()
        self.client = memcache.Client(memcache_config)

    def get_memcache_config(self):
        '''Try to get the config from Amazon in a short time.  If this
        fails, fall back to the existing config, or if there is none,
        to a dummy connection to localhost'''
        have_config = self.last_memcache_config is not None
        timeout = 0.5 if have_config else 5.0
        try:
            discovered = elasticache_auto_discovery.discover(
                self.elasticache_config, time_to_timeout=timeout)
        except socket.error:
            logger.warning('Could not fetch ElastiCache configuration for %s'
                           % self.elasticache_config, exc_info=True)
            if have_config:
                return self.last_memcache_config
            # return a dummy value
            logger.warning('No existing ElastiCache configuration for %s; '
                           'falling back to a dummy configuration'
                           % self.elasticache_config)
            return ['127.0.0.1:11211']
        # re-format for input to memcache.Client()
        memcache_config = ['%s:%s' % (e[1], e[2]) for e in discovered]
        self.last_memcache_config = memcache_config
        return memcache_config

    def checkout(self):
        if self.last_poll + self.POLL_INTERVAL < time.time():
            # reconfigure (this has the side-effect of marking dead
            # servers as live again)
            self.last_poll = time.time()
            memcache_config = self.get_memcache_config()
            self.client.set_servers(memcache_config)
        return self.client


class ElastiCacheFinder(MemcachedCacheFinder):

    client_wrapper_class = ElastiCacheClientWrapper


class CacheFinder(object):

    def __init__(self):
        self._finders = {
            'direct': DirectCacheFinder(),
            'elasticache': ElastiCacheFinder(),
            'mock': MockCacheFinder(),
        }

    @contextlib.contextmanager
    def cache(self, config):
        if isinstance(config, basestring):
            parsed = urlparse.urlparse(config)
            style = parsed.scheme
            config = parsed.netloc
        else:
            style = 'direct'

        mc, cookie = self._finders[style].acquire_cache(config)
        try:
            yield mc
        finally:
            self._finders[style].release_cache(cookie)


def init_app(app):
    app.memcached = CacheFinder()
