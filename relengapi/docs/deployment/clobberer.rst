Deploying Clobberer
===================

Database
--------

For historical reasons, clobberer uses its own RelengAPI database, named ``clobberer``.

Configuration
-------------

The configuration option `TASKCLUSTER_CACHES_TO_SKIP` gives a list of TaskCluster cache names that should not be clobbered or displayed to the user.

Permissions
-----------

Anyone can perform read-only operations against clobberer.
Only users with the ``clobberer.post.clobber`` permission can trigger clobber operations on workers.
