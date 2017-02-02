.. _services-shipit:

Service family: ``src/shipit_*``
================================

Shipit service family is a collection of smaller services with a common
frontend (``src/shipit_frontend``) interface.


``src/shipit_frontend``
-----------------------

:staging: https://shipit.staging.mozilla-releng.net
:production: https://shipit.mozilla-releng.net

Shipit frontend is a web interface, written in Elm, displaying to Mozilla Release Managers informations about:

- uplift requests for bugs on each Firefox release stage (Aurora, Beta, Release and ESR)
- automated merge tests
- detailed contributors informations

The goal of this project is to be fast, nice looking and always having up-to-date informations from multiple sources (Mozilla bugzilla, mercurial repository, patch analysis, ...)


``src/shipit_dashboard``
------------------------

:staging: https://dashboard.shipit.staging.mozilla-releng.net
:production: https://dashboard.shipit.mozilla-releng.net

Shipit Dashboard is the backend service storing and serving bug analysis for each Mozilla Firefox release versions: it's used by Shipit frontend.

Architecture:

- Python backend, written with Flask
- Hosted on Heroku (a dyno and Postgresql database)
- Stores analysis as Json in the postgresql database
- Authentication through Taskcluster (no local users)

.. note::

    There is no analysis or long running task in shipit dasthboard. It "just" stores data and serves it through a REST api.


``src/shipit_bot_uplift``
-------------------------

Shipit bot uplift is not a service, it's a Python bot, runnning as a Taskcluster hook every 30 minutes.
It does the following tasks on every run:

- Update a cached clone of mozilla-unified repository
- List current bugs on shipit_dashboard
- List current bugs for every release versions with an uplift request on Bugzilla
- Run a full bug analysis using libmozdata_ on every new bug (or bugs needing an update)
- Try to merge (through Mercurial graft) every patch in an uplift request
- Report the full analysis to shipit dashboard, so it can be displayed on shipit frontend.


.. _libmozdata: https://github.com/mozilla/libmozdata/
