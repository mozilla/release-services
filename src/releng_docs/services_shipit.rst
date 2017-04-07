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
-----------------------

Ship It Pipeline is a service that manages running pipelines. A pipeline is a series of steps that can depend on one
another and together represent some kind of workflow or process. The pipeline service is responsible for creating
instances of individual steps on the appropriate step service once that step is runnable. A step is runnable when all
its dependencies have finished.

A pipeline specifies the backend service URL and inputs for each step in the pipeline. This is so that the pipeline
service knows how to create specific steps when necessary.

Pipelines and Firefox releases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
NB. This section was written prior to having any pipelines implemented.

Initially we will integrate the legacy ship-it/release-runner infrastructure with the new pipelines.

1. release-runner will create a set of tasks in Taskcluster as normal
2. release-runner will then create a new pipeline and POST it to the pipeline service for execution. The pipeline will
   look roughly like this:

    .. blockdiag::

        blockdiag foo {
            B [label = "(B)uild"];
            S [label = "(S)ignoff"];
            P [label = "(P)ublish"];
            B -> S -> P;
        }


  B (Build) is a Taskcluster Step that waits for the tasks initially created by
  release-runner to finish

  S (Signoff) is a Signoff Step that waits for humans to approve the release

  P (Publish) is another Taskcluster Step that runs the in-tree decision task
  to generate the final set of tasks responsible for publishing the release.


3. The pipeline service will evaluate the pipeline and notice that step B is runnable, and so will create an instance
   of this step on the Taskcluster Step service. The pipeline service will then wait for the Taskcluster step to
   finish. Note that at this point the Signoff step S hasn't been created. It only exists in the pipeline definition.

4. Once B finishes, the pipeline service will create step S on the Signoff Step service. Again, the pipeline waits here
   for the signoff step to complete.

5. The Signoff Service will notify people that a signoff is required of them.

6. People sign-off on the step via Ship It's front-end.

7. The pipeline service sees that S is finished, and creates step P via the Taskcluster service.


Steps
-----

Step Services API
~~~~~~~~~~~~~~~~~

In order to ensure the Pipeline service can successfully managed Steps, each Step Service is required to implement the following API:
(TODO, flesh this out more)

- /

 - GET - Returns all steps with status (TODO: probably need pagination and filtering here)

- /{uid}

 - PUT - Create a new Step
 - DELETE - Remove the given Step

- /{uid}/definition

 - GET Returns the definition of the given step

- /{uid}/status

 - GET Returns the status of the given step.

  - Currently, one of: in_progress, success, failure, cancelled
  - Probably need to add support for including custom service-specific status info.

Step Services are free to add additional endpoints past the required ones.


``src/shipit_signoff``
~~~~~~~~~~~~~~~~~~~~~~

TODO


``src/shipit_taskcluster``
~~~~~~~~~~~~~~~~~~~~~~~~~~

TODO
