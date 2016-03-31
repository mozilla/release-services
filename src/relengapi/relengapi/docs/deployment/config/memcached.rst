.. _memcached-configuration:

Memcached
=========

Blueprints may require a memcached instance to cache data.
There is a common configuration syntax for this.

To use a normal memcached cluster, give the list of `"host:port"` pairs describing the servers::

    SOME_BLUEPRINT_CACHE = ['host-a.foo.com:11211', 'host-a.foo.com:11211']

To use Amazon ElastiCache, give a URL with scheme `elasticache` and the configuration endpoint::

    SOME_BLUEPRINT_CACHE = 'elasticache://mycachecluster2.b47jtf.cfg.use1.cache.amazonaws.com:11211'


