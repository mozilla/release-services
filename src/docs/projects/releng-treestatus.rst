.. _releng-treestatus-project:

Project: releng-treestatus
==========================


:Url:
  `production <https://treestatus.mozilla-releng.net>`_,
  `staging <https://treestatus.staging.mozilla-releng.net>`_
:Papertrail:
  `production <https://papertrailapp.com/groups/4472992/events?q=program%3Amozilla-releng%2Fservices%2Fproduction%2Freleng-treestatus>`_,
  `staging <https://papertrailapp.com/groups/4472992/events?q=program%3Amozilla-releng%2Fservices%2Fstaging%2Freleng-treestatus>`_
:Sentry:
  `production <https://sentry.prod.mozaws.net/operations/mozilla-releng-services/?query=environment%3Aproduction+site%3Areleng-treestatus+>`_,
  `staging <https://sentry.prod.mozaws.net/operations/mozilla-releng-services/?query=environment%3Astaging+site%3Areleng-treestatus+>`_
:Heroku:
  `production <https://dashboard.heroku.com/apps/releng-production-treestatus>`_,
  `staging <https://dashboard.heroku.com/apps/releng-staging-treestatus>`_
:Database (PostreSQL):
  `production <https://data.heroku.com/datastores/dad34d86-54d0-46fc-911e-82768c73f247>`_,
  `staging <https://data.heroku.com/datastores/81feab6a-0a7c-4489-a6a1-9c0106c5e0ea>`_
:Cache (Redis):
  `production <https://data.heroku.com/datastores/04b0b822-a806-475b-a397-38df291284fc>`_,
  `staging <https://data.heroku.com/datastores/6f5e3490-0e46-4e7b-89d1-abbfb1fd9026>`_
:Contact: `Rok Garbas`_, (backup `Release Engineering`_)


TreeStatus is a relatively simple tool to keep track of the status of the
**trees** at Mozilla.

**A tree** is a version-control repository, and can generally be in one of
three states: **open**, **closed**, or **approval-required**. These states
affect the ability of developers to push new commits to these repositories.
Trees typically close when something prevents builds and tests from succeeding.

The tree status tool provides an interface for **anyone to see the current
status of all trees**. It also allows "sheriffs" to manipulate tree status.


Giving permission/roles to Sherrifs to close/open trees
-------------------------------------------------------

A common request one administrator of ``releng-treestatus`` would receive is to
give permission for new 

Certain JSON API endpoints are protected by `Taskcluster scopes`_ (for details
which endpoint is protected by you can look at ``api.py``). Those scopes
(permissions) are grouped in two roles:

#. **Admin role**

  Administrator role has all the permissions (scopes) that are available.
  Administrator can create, update and remove trees. By default this role is
  assigned to everybody that is in `vpn_sheriff`_ LDAP group.

  To assign **admin role** to certain user/group you need to add
  ``assume:project:releng:treestatus/admin`` scope to that user/group.

  Roles / Clients with **admin role** are listed `here
  <https://tools.taskcluster.net/auth/scopes/assume%3Aproject%3Areleng%3Atreestatus%2Fadmin>`_.

#. **Sheriff role**

  Sheriff role the permissions (scopes) to update status of the trees and to
  revert those updates. This role is usually given to *sheriff's deputies* to
  be able to close/open certain trees.

  Roles / Clients with **admin role** are listed `here
  <https://tools.taskcluster.net/auth/scopes/assume%3Aproject%3Areleng%3Atreestatus%2Fsheriff>`_.



Troubleshooting
---------------

In case of an incident this five steps that should help you narrow down the
problem.

#. Look at `Heroku metrics
   <https://dashboard.heroku.com/apps/releng-production-treestatus/metrics/web>`_
   to get birds view on the running application.

#. There might be some problems with Heroku. Make sure to also check their
   `status page <https://status.heroku.com>`_

#. Check if there is any unsual high count of errors collected in Sentry.

#. To see more logs (from the past) look at Papertrail.

#. Sometimes restarting an application might solve the issue (at least
   temporary). Once you restart the application also verify that it is working
   correctly (follow :ref:`instructions below <verify-releng-treestatus>`).


Deploying
---------

``releng-treestatus`` is a Flask application deployed to Heroku. Please follow
the :ref:`Heroku deployment guide <deploy-heroku-target>` how to manually
deploy hotfixes.

The architecture

.. blockdiag::
    :align: center

    orientation = portrait

    A [ label = "URL: https://mozilla-releng.net/treestatus\nPROJECT: releng-frontend\nTARGET: AWS S3"
      , width = 280
      , height = 60
      ];

    B [ label = "https://treestatus.mozilla-releng.net/\nreleng-treestatus on Heroku"
      , width = 280
      , height = 60
      ];

    C [ label = "PostgreSQL\nTARGET: Heroku"
      , width = 180
      , height = 60
      ];

    A -> B -> C



Is TreeStatus working correctly?
--------------------------------

.. _verify-releng-treestatus:

**To test and verify** that ``releng-treestatus`` is running correctly please
follow the following steps:

#. Select which environement (production or staging).

   For production:

   .. code-block:: console

       $ export URL=https://treestatus.mozilla-releng.net

   For staging:

   .. code-block:: console

       $ export URL=https://treestatus.staging.mozilla-releng.net

#. List all trees

   .. code-block:: console

       $ curl $URL/trees
       {
          "result": {
            "ash": {
              "message_of_the_day": "MotDs are a nice thing we can't have.",
              "reason": "",
              "status": "open",
              "tree": "ash"
            },
            ...
          }
       }

#. Show details of an existing tree

   .. code-block:: console

       $ curl $URL/trees/mozilla-beta
       {
         "result": {
           "message_of_the_day": "",
           "reason": "",
           "status": "approval required",
           "tree": "mozilla-beta"
         }
       }


#. Show error for non existing tree (return code: 404)

   .. code-block:: console

       $ curl $URL/trees/invalid
       {
         "detail": "No such tree",
         "instance": "about:blank",
         "status": 404,
         "title": "404 Not Found: No such tree",
         "type": "about:blank"
       }


Develop
-------

To start developing ``releng-treestatus`` you would need to:

#. Install all :ref:`requirements <develop-requirements>` and read through
   general :ref:`guide how to contribute <develop-contribute>`.

#. Read through :ref:`python projects guide <develop-python-project>`, how
   python projects are structured and how to add/update dependencies to
   a project.

#. And last you will have to read about conventions we use to :ref:`write REST
   endpoints using Flask <develop-flask-project>`.

   It is important to know that ``releng-treestatus`` uses the following
   Flask extensions:

   - :ref:`log <develop-flask-log-extension>` (centralize logging),
   - :ref:`security <develop-flask-security-extension>` (HTTP security headers),
   - :ref:`cors <develop-flask-cors-extension>` (setting CORS headers who can
     access this url),
   - :ref:`api <develop-flask-api-extension>` (swagger/openapi integration),
   - :ref:`auth <develop-flask-auth-extension>` (authentication and
     authorization via `Taskcluster Auth service`_),
   - :ref:`db <develop-flask-db-extension>` (convinience utilities how to work
     with `SQLAlchemy`_),
   - :ref:`cache <develop-flask-cache-extension>` (integration with
     Flask-Cache),
   - :ref:`pulse <develop-flask-pulse-extension>` (convinience utilities to
     work with Pulse_)



.. _`Rok Garbas`: https://phonebook.mozilla.org/?search/Rok%20Garbas
.. _`Release Engineering`: https://wiki.mozilla.org/ReleaseEngineering#Contacting_Release_Engineering
.. _`SQLAlchemy`: https://pypi.python.org/pypi/SQLAlchemy
.. _`Taskcluster Auth service`: https://docs.taskcluster.net/reference/platform/taskcluster-auth
.. _`Pulse`: https://wiki.mozilla.org/Auto-tools/Projects/Pulse
.. _`vpn_sheriff`: https://tools.taskcluster.net/auth/roles/mozilla-group%3Avpn_sheriff
.. _`Taskcluster scopes`: https://docs.taskcluster.net/presentations/scopes/
