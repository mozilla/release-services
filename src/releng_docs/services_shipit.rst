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


ShipIt v1 and v2 interaction
----------------------------

Initially, Shipit v2 will compliment v1 by adding features, as opposed to
replacing. The following is a implementation strategy for how that will work.

ShipIt v1 will solely be responsible for submitting and kicking off a new
release.

.. code-block:: console

    % curl -X POST -d "product=firefox&version=99.0" https://ship-it.mozilla.org/submit_release.html

releaserunner_ continues to behave as normal by polling ShipIt v1 for new
releases and, when found, runs release_sanity_, creates taskcluster_graph1_,
and notifies release-drivers of new release.

In addition, releaserunner will tell Shipit v2 about the new release and ask
Shipit v2 to create a pipeline:


.. code-block:: python

    r = requests.post(
        'https://pipeline.shipit.mozilla-releng.net',
        data={uid='foo', pipeline={}},
    )

Shipit v2's pipeline will consist of steps representing the release. Example
steps are (1) :ref:`signoff steps <shipit_signoff>` and (2) :ref:`taskcluster
steps <shipit_taskcluster>`.

Shipit v2 will also create a step for the Shipit v1 generated taskcluster graph
(graph1) so that it can add that graph to the Shipit v2 pipeline as
a dependency. This means that a taskcluster step can be passed an existing
taskcluster graphid to track rather than always creating a new one.

How Shipit v1 taskcluster graph1 will differ?

Since graph1 is created by Shipit v1 and includes taskcluster tasks for doing
sign offs and publishing releases, it will need to be trimmed and then offload
its later tasks to Shipit v2 via subsequent steps within the pipeline.

And so, initially, graph1 will create all required tasks up until the first
human sign off. This is easily defined by: *the first "human decision task"
within the graph*.

For example, here is an overview of what a Beta release comprises of in
simplified form:

.. blockdiag::
   :align: center

   diagram {
     orientation = portrait;
     default_fontsize = 16;


     A [ label = "generate release\nartifacts"
       , width = 180
       , height = 60
       ];
     B [ label = "verify artifacts\nand updates on\ntest channel"
       , width = 180
       , height = 80
       ];
     C [ label = "push artifacts to\nrelease location"
       , width = 180
       , height = 60
       ];
     D [ label = "publish release\nhuman sign off"
       , width = 180
       , height = 60
       ];
     E [ label = "publish release"
       , width = 180
       ];

     A -> B -> C -> D -> E;
   }


In the beta case, graph1 would finish with *push artifacts to release
location*. There would then be a Shipit v2 pipeline consisting of a sign off
step: *publish release human sign off*, and a taskcluster step: *publish
release*

The taskcluster *publish release* step would comprise of the following tasks:
publishing on balrog, bumping next version, updating bouncer, and informing
Shipit v1 the release is complete (mark as shipped).

Release candidates would be implemented in a similar manner but since it
contains more sign offs, Shipit v1 would offload more tasks to Shipit v2


.. _releaserunner: https://dxr.mozilla.org/build-central/search?q=path%3Apuppet%2Fmanifests%2Fmoco-nodes+releaserunner&redirect=false
.. _release_sanity: https://hg.mozilla.org/build/tools/file/c85a80e0c3e4/buildfarm/release/release-runner.py#l353
.. _taskcluster_graph1: https://hg.mozilla.org/build/tools/file/c85a80e0c3e4/buildfarm/release/release-runner.py#l501


Authentication and authorization
--------------------------------

ShipIt (and services as a whole) will not rely on solely auth0 or current
Taskcluster auth/scopes. Instead, ShipIt will use a combination of the two.

Actual implementation design will be implemented, at least initially, as
follows:

#. Initial login and authentication will continue to be through Taskcluster
   throughout services including ShipIt_*. Taskcluster scopes will be used for
   protecting frontend visibility, and backend permissions (authorization) for
   everything bar resolving a signoff step in ShipIt_signoff.

#. ShipIt_signoff has some added protection. Since Taskcluster auth, as it's
   currently implemented, can not reliably guarantee the client is who they
   claim to be, ShipIt_signoff will have an additional login via auth0 as well
   as support for MFA. Authorization for signing off will likely be managed by
   LDAP permissions connected to auth0.


.. _client: https://tools.taskcluster.net/auth/clients/
.. _roles: https://tools.taskcluster.net/auth/roles/


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


``src/shipit_signoff``
----------------------

TODO


``src/shipit_taskcluster``
--------------------------

TODO


Steps
=====


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

