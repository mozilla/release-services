Deploying Clobberer
===================

Database
--------

For historical reasons, clobberer uses its own RelengAPI database, named ``clobberer``.

Configuration
-------------

The configuration option `TASKCLUSTER_CACHES_TO_SKIP` gives a list of TaskCluster cache names that should not be clobbered or displayed to the user.

Clobberer calls out to TaskCluster, so it needs a ``TASKCLUSTER_CLIENT_ID`` and ``TASKCLUSTER_ACCESS_TOKEN`` granting ``purge-cache:<provisionerId>/<workerType>:<cacheName>`` for the appropriate workerTypes.

Finally, the contents of the most recent decision tasks are cached for ``TASKCLUSTER_CACHE_DURATION`` seconds, defaulting to 5 minutes.

Permissions
-----------

Anyone can perform read-only operations against clobberer.
Only users with the ``clobberer.post.clobber`` permission can trigger clobber operations on workers.
