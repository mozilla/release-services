.. _services-shipit:

Service family: ``src/shipit_*``
================================

The Ship It family is a collection of smaller services that help us build, ship, and maintain Releases. There are a few different types of services:

* Frontend - This is where all user interaction with Ship It happens
* Pipeline - The Pipeline service is responsible for managing the end to end process of shipping a Release
* Steps - Step services implement discrete parts of a Pipeline
* Bots - Bots run regularly and are responsible for collecting information required by Ship It

``src/shipit_frontend``
-----------------------

:staging: https://shipit.staging.mozilla-releng.net
:production: https://shipit.mozilla-releng.net

Ship It frontend is a web interface, written in Elm, displaying to Mozilla Release Managers informations about:

- uplift requests for bugs on each Firefox release stage (Aurora, Beta, Release and ESR)
- automated merge tests
- detailed contributors informations

The goal of this project is to be fast, nice looking and always having up-to-date informations from multiple sources (Mozilla bugzilla, mercurial repository, patch analysis, ...)


``src/shipit_uplift``
------------------------

:staging: https://dashboard.shipit.staging.mozilla-releng.net
:production: https://dashboard.shipit.mozilla-releng.net

Ship It Uplift is the backend service storing and serving bug analysis for each Mozilla Firefox release versions: it's used by Ship It frontend.

Architecture:

- Python backend, written with Flask
- Hosted on Heroku (a dyno and Postgresql database)
- Stores analysis as Json in the postgresql database
- Authentication through Taskcluster (no local users)

.. note::

    There is no analysis or long running task in shipit dashboard. It "just" stores data and serves it through a REST api.


``src/shipit_bot_uplift``
-------------------------

Ship It bot uplift is not a service, it's a Python bot, runnning as a Taskcluster hook every 30 minutes.
It does the following tasks on every run:

- Update a cached clone of mozilla-unified repository
- List current bugs on shipit_uplift
- List current bugs for every release versions with an uplift request on Bugzilla
- Run a full bug analysis using libmozdata_ on every new bug (or bugs needing an update)
- Try to merge (through Mercurial graft) every patch in an uplift request
- Report the full analysis to shipit dashboard, so it can be displayed on shipit frontend.


.. _libmozdata: https://github.com/mozilla/libmozdata/


``src/shipit_pipeline``

TODO


Steps
-----

Step Services API
~~~~~~~~~~~~~~~~~

In order to ensure the Pipeline service can successfully managed Steps, each Step Service is required to implement the following API:
(TODO, flesh this out more)

* /
** GET - Returns all steps with status (TODO: probably need pagination and filtering here)
* /{uid}
** PUT - Create a new Step
** DELETE - Remove the given Step
* /{uid}/definition
** GET Returns the definition of the given step
* /{uid}/status
** GET Returns the status of the given step.
*** Currently, one of: in_progress, success, failure, cancelled
*** Probably need to add support for including custom service-specific status info.

Step Services are free to add additional endpoints past the required ones.


``src/shipit_signoff``
~~~~~~~~~~~~~~~~~~~~~~

TODO


``src/shipit_taskcluster``
~~~~~~~~~~~~~~~~~~~~~~~~~~

TODO
