Mozilla Release Engineering Services
====================================

A goal of *Release Engineering Services* is to *converge efforts* to
**develop**, **test**, **deploy**, **maintain**, and most importantly
**document** all projects that *Release Engineering Team* is providing or
supporting.

:Code: https://github.com/mozilla/release-services
:Issues: https://github.com/mozilla/release-services/issues
:Documentation: https://docs.mozilla-releng.net


.. Introduction
.. ------------
.. 
.. .. raw:: html
.. 
..     <iframe src="https://player.vimeo.com/video/218952258"
..             width="640" height="480" frameborder="0"
..             webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>


Projects
--------

.. toctree::
    :maxdepth: 1

    docs <projects/docs>
    releng-frontend <projects/releng-frontend>
    mapper <projects/mapper>
    notification <projects/notification>
    tooltool <projects/tooltool>
    treestatus <projects/treestatus>
    codecoverage/bot <projects/codecoverage-bot>
    codecoverage/backend <projects/codecoverage-backend>
    codecoverage/crawler <projects/codecoverage-crawler>
    shipit/frontend <projects/shipit-frontend>
    staticanalysis/bot <projects/staticanalysis-bot>
    pulselistener <projects/pulselistener>
    uplift/backend <projects/uplift-backend>
    uplift/frontend <projects/uplift-frontend>
    uplift/bot <projects/uplift-bot>


Develop
-------

.. toctree::
    :maxdepth: 2

    develop/contribute
    develop/python-project
    develop/flask-project
    develop/install-nix
    develop/branching-policy
    develop/defending-design


Deploy
------

.. toctree::
    :maxdepth: 2

    deploy/weekly-releases
    deploy/heroku-target
    deploy/s3-target
    deploy/taskcluster-hook-target
    deploy/configure-dns
