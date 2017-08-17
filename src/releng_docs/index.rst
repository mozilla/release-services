Mozilla Release Engineering Services
====================================

A goal of *Release Engineering Services* is to *converge efforts* to
**develop**, **test**, **deploy**, **maintain**, and most importantly
**document** all projects that *Release Engineering Team* is providing or
supporting.

Currently supported development platform are **Linux** (via Nix) or any
platform that runs **Docker**.

:Code: https://github.com/mozilla-releng/services
:Issues: https://github.com/mozilla-releng/services/issues
:Documentation: https://docs.mozilla-releng.net


Introduction
------------

.. raw:: html

    <iframe src="https://player.vimeo.com/video/218952258" width="640" height="480" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>


Projects
--------

.. toctree::
    :maxdepth: 1

    releng-docs <projects/releng-docs>
    releng-frontend <projects/releng-frontend>
    releng-notification-identity <projects/releng-notification-identity>
    releng-notification-policy <projects/releng-notification-policy>
    releng-tooltool <projects/releng-tooltool>
    releng-treestatus <projects/releng-treestatus>
    shipit-bot-uplift <projects/shipit-bot-uplift>
    shipit-frontend <projects/shipit-frontend>
    shipit-uplift <projects/shipit-uplift>


Develop
-------

.. toctree::
    :maxdepth: 2

    develop/contribute
    develop/python-project
    develop/flask-project
    develop/install-nix
    develop/defending_design


Deploy
------

.. toctree::
    :maxdepth: 2

    deploy/weekly_releases
    deploy/heroku-target
    deploy/s3-target
    deploy/taskluster-hook-target

