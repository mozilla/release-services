.. _releng-tooltool-project:

Project: releng-tooltool
========================

:Url:
  `production <https://tooltool.mozilla-releng.net>`_,
  `staging <https://tooltool.staging.mozilla-releng.net>`_
:Papertrail:
  `production <https://papertrailapp.com/groups/4472992/events?q=program%3Amozilla-releng%2Fservices%2Fproduction%2Freleng-tooltool>`_,
  `staging <https://papertrailapp.com/groups/4472992/events?q=program%3Amozilla-releng%2Fservices%2Fstaging%2Freleng-tooltool>`_
:Sentry:
  `production <https://sentry.prod.mozaws.net/operations/mozilla-releng-services/?query=environment%3Aproduction+site%3Areleng-tooltool+>`_,
  `staging <https://sentry.prod.mozaws.net/operations/mozilla-releng-services/?query=environment%3Astaging+site%3Areleng-tooltool+>`_
:Heroku:
  `production <https://dashboard.heroku.com/apps/releng-production-tooltool>`_,
  `staging <https://dashboard.heroku.com/apps/releng-staging-tooltool>`_
:Database (PostreSQL):
  `production <https://data.heroku.com/datastores/dad34d86-54d0-46fc-911e-82768c73f247>`_,
  `staging <https://data.heroku.com/datastores/81feab6a-0a7c-4489-a6a1-9c0106c5e0ea>`_
:Contact: `Rok Garbas`_, (backup `Release Engineering`_)


Some of the jobs in the RelEng infrastructure make use of generic binary
artifacts, which are stored in dedicated artifacts repositories (S3 buckets).
``releng-tooltool`` application provides an interface to those artifacts
repositories.


.. todo:: write about relengapi tokenauth

Troubleshooting
---------------

In case of an incident this five steps that should help you narrow down the
problem.

#. Look at `Heroku metrics
   <https://dashboard.heroku.com/apps/releng-production-tooltool/metrics/web>`_
   to get birds view on the running application.

#. There might be some problems with Heroku. Make sure to also check their
   `status page <https://status.heroku.com>`_

#. Check if there is any unsual high count of errors collected in Sentry.

#. To see more logs (from the past) look at Papertrail.

#. Sometimes restarting an application might solve the issue (at least
   temporary). Once you restart the application also verify that it is working
   correctly (follow :ref:`instructions below <verify-releng-tooltool>`).


Deploying
---------

``releng-tooltool`` is a Flask application deployed to Heroku. Please follow
the :ref:`Heroku deployment guide <deploy-heroku-target>` how to manually
deploy hotfixes.

The architecture

.. blockdiag::
    :align: center

    orientation = portrait

    B [ label = "https://tooltool.mozilla-releng.net/\nreleng-tooltool on Heroku"
      , width = 280
      , height = 60
      ];

    C [ label = "PostgreSQL\nTARGET: Heroku"
      , width = 180
      , height = 60
      ];

    B -> C


Is ToolTool working correctly?
------------------------------

.. _verify-releng-tooltool:

**To test and verify** that ``releng-tooltool`` is running correctly please
follow the following steps:

#. Select which environement (production or staging).

   For production:

   .. code-block:: console

       $ export URL=https://tooltool.mozilla-releng.net

   For staging:

   .. code-block:: console

       $ export URL=https://tooltool.staging.mozilla-releng.net

#. Known public sha512 should redirect (return code: 302)

   .. code-block:: console

       $ curl $URL/sha512/f93a685c8a10abbd349cbef5306441ba235c4cbfba1cc000299e11b58f258e9953cbe23463515407925eeca94c3f5d8e5f637c95be387e620845efa43cdcb0c0
       <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
       <title>Redirecting...</title>
       <h1>Redirecting...</h1>
       <p>You should be redirected automatically to target URL: <a href="..."></a>.  If not click the link.% 

#. Known private sha512 should stay protected (return code: 403)

   .. code-block:: console

      $ curl $URL/sha512/edf96781042db513700c4a092ef367c05933967b036db9b0f716b75da613a7eaea055d0f60b1e12f6e41a545962cec97a7b78c6b86363ee1ec7a9f42699a5531
      {
         "detail": "You don't have the permission to access the requested resource. It is either read-protected or not readable by the server.", 
         "instance": "about:blank", 
         "status": 403, 
         "title": "403 Forbidden: You don't have the permission to access the requested resource. It is either read-protected or not readable by the server.", 
         "type": "about:blank"
       }

#. Unknown sha512 should return invalid error (return code: 400)

   .. code-block:: console

       $ curl $URL/sha512/invalid
       {
         "detail": "Invalid sha512 digest", 
         "instance": "about:blank", 
         "status": 400, 
         "title": "400 Bad Request: Invalid sha512 digest", 
         "type": "about:blank"
       }


Develop
-------

To start developing ``releng-tooltool`` you would need to:

#. Install all :ref:`requirements <develop-requirements>` and read through
   general :ref:`guide how to contribute <develop-contribute>`.

#. Read through :ref:`python projects guide <develop-python-project>`, how
   python projects are structured and how to add/update dependencies to
   a project.

#. And last you will have to read about conventions we use to :ref:`write REST
   endpoints using Flask <develop-flask-project>`.

   It is important to know that ``releng-tooltool`` uses the following
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


.. _`Rok Garbas`: https://phonebook.mozilla.org/?search/Rok%20Garbas
.. _`Release Engineering`: https://wiki.mozilla.org/ReleaseEngineering#Contacting_Release_Engineering
.. _`Taskcluster Auth service`: https://docs.taskcluster.net/reference/platform/taskcluster-auth
.. _`SQLAlchemy`: https://pypi.python.org/pypi/SQLAlchemy
