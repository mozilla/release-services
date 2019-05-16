.. _tooltool-project:

Project: ToolTool
=================

:Contact: `Rok Garbas`_, (backup `Release Engineering`_)

.. _`Rok Garbas`: https://phonebook.mozilla.org/?search/Rok%20Garbas
.. _`Release Engineering`: https://wiki.mozilla.org/ReleaseEngineering#Contacting_Release_Engineering

Tasks in the RelEng infrastructure and make use of generic binary artifacts,
which are stored in dedicated artifacts repositories (S3 buckets). ToolTool
application provides an interface to those artifacts repositories.


Request authentication credentials for the client (tooltool.py)
---------------------------------------------------------------

`Open a bug on bugzila`_ and request new taskcluster client credentials that
that you will then use in.

Use the following points to guide you opening the bug:

#. **Product** field should be ``Release Engineering``
#. **Component** field should be ``Applications: ToolTool``
#. **Summary** field should be ``Requesting taskcluster client credentials to use with tooltoo.py``
#. **Description** field should contain:

   - who is the responsible person and which is the responsible team
   - what is the purpose of usage
   - what should be the expiration date of the credentials (suggested is one year)
   - which level of access is required:
     - Download PUBLIC files from tooltool.
     - Download INTERNAL files from tooltool.
     - Upload PUBLIC files to tooltool.
     - Upload INTERNAL files to tooltool.
     - Manage tooltool files, including deleting and changing visibility levels.


.. _`Open a bug on bugzila`: https://bugzilla.mozilla.org/enter_bug.cgi?product=Release%20Engineering&component=Applications%3A%20ToolTool


How to generate taskcluster client credentials
----------------------------------------------

#. Go to https://tools.taskcluster.net/auth/clients.

#. Make sure you are logged into taskcluster.

#. Fill the ``Create New Client`` form:
   
   :ClientId: Make sure to include the Bug number by following the template ``project/releng/services/tooltool/bug<NUMBER>``.
   :Description: Who is responsible and which team, also where is this token used.
   :Expires: Requested expiration, by default set it to 1 year.
   :Client Scopes: List of scopes requested based on the requested level of access:

      - Download PUBLIC files from tooltool
        (``project:releng:services/tooltool/api/download/public``).
      - Download INTERNAL files from tooltool
        (``project:releng:services/tooltool/api/download/internal``).
      - Upload PUBLIC files to tooltool
        (``project:releng:services/tooltool/api/upload/public``).
      - Upload INTERNAL files to tooltool
        (``project:releng:services/tooltool/api/upload/internal``).
      - Manage tooltool files, including deleting and changing visibility levels
        (``project:releng:services/tooltool/api/manage``).


Troubleshooting deployment
--------------------------

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
   correctly (follow :ref:`instructions below <verify-tooltool>`).


How to check if ToolTool is working correctly?
----------------------------------------------

.. _verify-tooltool:

**To test and verify** that the JSON API is running correctly please
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

      $ curl $URL/sha512/06a1cf7b1918ffd94210e8089cf48985fbf9af95f15cd9dd5007df76b934c2b825147334ba176c3f19a9f7d86585c58e017bc23a606e8831872c8b40560be874
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

To start developing ``tooltool/api`` you would need to:

#. Install all :ref:`requirements <develop-requirements>` and read through
   general :ref:`guide how to contribute <develop-contribute>`.

#. Read through :ref:`python projects guide <develop-python-project>`, how
   python projects are structured and how to add/update dependencies to
   a project.

#. And last you will have to read about conventions we use to :ref:`write REST
   endpoints using Flask <develop-flask-project>`.

   It is important to know that ``tooltool/api`` uses the following
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


.. _`Taskcluster Auth service`: https://docs.taskcluster.net/reference/platform/taskcluster-auth
.. _`SQLAlchemy`: https://pypi.python.org/pypi/SQLAlchemy
