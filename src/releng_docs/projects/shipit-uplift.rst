.. _shipit-uplift-project:

Project: shipit-uplift
======================

:production: https://uplift.shipit.mozilla-releng.net
:staging: https://upligt.shipit.staging.mozilla-releng.net
:contact: `Bastien Abadie`_, (backup `Release Engineering`_)

ShipIt Uplift is the backend service storing and serving bug analysis for each
Mozilla Firefox release versions: it's used by ShipIt frontend.

Architecture:

- Python backend, written with Flask
- Hosted on Heroku (a dyno and Postgresql database)
- Stores analysis as Json in the postgresql database
- Authentication through Taskcluster (no local users)

.. note::

    There is no analysis or long running task in shipit dashboard. It "just"
    stores data and serves it through a REST api.


.. _`Bastien Abadie`: https://github.com/La0
.. _`Release Engineering`: https://wiki.mozilla.org/ReleaseEngineering#Contacting_Release_Engineering

