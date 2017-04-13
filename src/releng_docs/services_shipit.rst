.. _services-shipit:

Service family: ``src/shipit_*``
================================


**The ShipIt family** is a collection of smaller services that help us build,
ship, and maintain Releases.

There are a few different types of services:

#. **FRONTEND**
   
   This is one single page application for all of the our backend services.
   This is also where all user interaction with ShipIt happens.

#. **BACKENDS**
   
   This are JSON API endpoints that have specific functionality.

#. **PIPELINE STEPS**

   One of the backends is a pipeline service (``src/shipit_pipeline``) which is
   responsible to start, stop and monitor **pipeline steps services**, which
   are special kind of backend services.

#. **BOTS**

  Bots are schedules Taskcluster tasks that run regularly and are responsible
  for collecting information required by ShipIt.



.. _shipit_frontend:

Frontend (``src/shipit_frontend``)
----------------------------------

.. todo:: need to rewrite this section

:staging: https://shipit.staging.mozilla-releng.net
:production: https://shipit.mozilla-releng.net

ShipIt frontend is a web interface, written in Elm, displaying to Mozilla
Release Managers informations about:

- uplift requests for bugs on each Firefox release stage (Aurora, Beta, Release
  and ESR)

- automated merge tests

- detailed contributors informations

The goal of this project is to be fast, nice looking and always having
up-to-date informations from multiple sources (Mozilla bugzilla, mercurial
repository, patch analysis, ...)
Back



Backends
--------

.. todo:: in short explain what a backend is also point to general backend
          documentation


.. _shipit_pipeline:

``src/shipit_pipeline``
^^^^^^^^^^^^^^^^^^^^^^^

.. todo::

    This section was written prior to having any pipelines implemented.

    When pipeline is implemented write a final documentation.

ShipIt Pipeline is a service that manages running pipelines. A pipeline is
a series of steps that can depend on one another and together represent some
kind of workflow or process. The pipeline service is responsible for creating
instances of individual steps on the appropriate step service once that step is
runnable. A step is runnable when all its dependencies have finished.

A pipeline specifies the backend service URL and inputs for each step in the
pipeline. This is so that the pipeline service knows how to create specific
steps when necessary.


Pipelines and Firefox releases
******************************

Initially we will integrate the legacy ship-it/release-runner infrastructure
with the new pipelines.

#. release-runner will create a set of tasks in Taskcluster as normal

#. release-runner will then create a new pipeline and POST it to the pipeline
   service for execution. The pipeline will look roughly like this:

    .. blockdiag::

        blockdiag foo {
            B [label = "(B)uild"];
            S [label = "(S)ignoff"];
            P [label = "(P)ublish"];
            B -> S -> P;
        }

  .. todo:: convert below list to blockdiag table

  - **B (Build)** is a Taskcluster Step that waits for the tasks initially
    created by release-runner to finish.

  - **S (Signoff)** is a Signoff Step that waits for humans to approve the
    release.

  - **P (Publish)** is another Taskcluster Step that runs the in-tree decision
    task to generate the final set of tasks responsible for publishing the
    release.


#. The pipeline service will evaluate the pipeline and notice that step B is
   runnable, and so will create an instance of this step on the Taskcluster
   Step service. The pipeline service will then wait for the Taskcluster step
   to finish. Note that at this point the Signoff step S hasn't been created.
   It only exists in the pipeline definition.

#. Once B finishes, the pipeline service will create step S on the Signoff Step
   service. Again, the pipeline waits here for the signoff step to complete.

#. The Signoff Service will notify people that a signoff is required of them.

#. People sign-off on the step via ShipIt's front-end.

#. The pipeline service sees that S is finished, and creates step P via the
   Taskcluster service.


Steps
-----

In order to ensure the Pipeline service can successfully managed Steps, each
Step Service is required to implement the following API: (TODO, flesh this out
more)

.. todo:: once implemented point to api.yml

.. todo:: it would be much more usefull to show `sequence diagram`_ of how
          pipeline <-> steps interact. once final implementation lands.

.. _`sequence diagram`: http://blockdiag.com/en/seqdiag/index.html

Step API:

- /

 - GET - Returns all steps with status (TODO: probably need pagination and
   filtering here)

- /{uid}

 - PUT - Create a new Step

 - DELETE - Remove the given Step

- /{uid}/definition

 - GET Returns the definition of the given step

- /{uid}/status

 - GET Returns the status of the given step.

  - Currently, one of: in_progress, success, failure, cancelled

  - Probably need to add support for including custom service-specific status
    info.

Step Services are free to add additional endpoints past the required ones.


.. _shipit_signoff:

``src/shipit_signoff``
^^^^^^^^^^^^^^^^^^^^^^

.. include:: shipit_signoffs/shipit-signoffs.rst


.. _shipit_taskcluster:

``src/shipit_tackluster``
^^^^^^^^^^^^^^^^^^^^^^^^^


.. _shipit_uplift:

``src/shipit_uplift``
^^^^^^^^^^^^^^^^^^^^^


:staging: https://dashboard.shipit.staging.mozilla-releng.net
:production: https://dashboard.shipit.mozilla-releng.net

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


Bots
----

.. _shipit_bot_uplift:

``src/shipit_bot_uplift``
^^^^^^^^^^^^^^^^^^^^^^^^^

ShipIt bot uplift is not a service, it's a Python bot, runnning as
a Taskcluster hook every 30 minutes.

It does the following tasks on every run:

- Update a cached clone of mozilla-unified repository

- List current bugs on shipit_uplift

- List current bugs for every release versions with an uplift request on
  Bugzilla

- Run a full bug analysis using libmozdata_ on every new bug (or bugs needing
  an update)

- Try to merge (through Mercurial graft) every patch in an uplift request

- Report the full analysis to shipit dashboard, so it can be displayed on
  shipit frontend.


.. _libmozdata: https://github.com/mozilla/libmozdata/


.. _shipit_code_coverage:

``src/shipit_code_coverage``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. _shipit_pulse_listener:

``src/shipit_pulse_listener``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. _shipit_risk_assessment:

``src/shipit_risk_assessment``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. _shipit_static_analysis:

``src/shipit_static_analysis``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. target-notes::
