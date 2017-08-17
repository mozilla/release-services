.. _releng-tooltool-project:

Project: releng-tooltool
========================

:production: https://tooltool.mozilla-releng.net
:staging: https://tooltool.staging.mozilla-releng.net
:contact: `Rok Garbas`_, (backup `Release Engineering`_)

Some of the jobs in the RelEng infrastructure make use of generic binary
artifacts, which are stored in dedicated artifacts repositories (S3 buckets).
``releng-tooltool`` application provides an interface to those artifacts
repositories.

All levels of logs are collected in Papertrails (
`production <https://papertrailapp.com/groups/4472992/events?q=program%3Amozilla-releng%2Fservices%2Fproduction%2Freleng-tooltool>`_,
`staging <https://papertrailapp.com/groups/4472992/events?q=program%3Amozilla-releng%2Fservices%2Fstaging%2Freleng-tooltool>`_ ),
warning and errors logs are agregated in Sentry (
`production <https://sentry.prod.mozaws.net/operations/mozilla-releng-services/?query=environment%3Aproduction+site%3Areleng-tooltool+>`_,
`staging <https://sentry.prod.mozaws.net/operations/mozilla-releng-services/?query=environment%3Astaging+site%3Areleng-tooltool+>`_ )
and application is running on Heroku (
`production <https://dashboard.heroku.com/apps/releng-production-tooltool>`_,
`staging <https://dashboard.heroku.com/apps/releng-staging-tooltool>`_ ).

**To start developing** ``releng-tooltool`` please follow :ref:`development
guide <develop-flask-project>`.

**To (re)deploy** ``releng-tooltool`` to Heroku please follow :ref:`deployment
guide <deploy-heroku-target>`.

**To test (verify)** that ``releng-tooltool`` is running correctly please follow the
following steps:

#. Known public sha512 should redirect (return code: 302)

   .. code-block:: console

       $ curl -X GET --header 'Accept: application/json' 'https://tooltool.mozilla-releng.net/sha512/f93a685c8a10abbd349cbef5306441ba235c4cbfba1cc000299e11b58f258e9953cbe23463515407925eeca94c3f5d8e5f637c95be387e620845efa43cdcb0c0'
       <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
       <title>Redirecting...</title>
       <h1>Redirecting...</h1>
       <p>You should be redirected automatically to target URL: <a href="..."></a>.  If not click the link.% 

#. Known private sha512 should stay protected (return code: 403)

   .. code-block:: console

      $ curl -X GET --header 'Accept: application/json' 'https://tooltool.mozilla-releng.net/sha512/edf96781042db513700c4a092ef367c05933967b036db9b0f716b75da613a7eaea055d0f60b1e12f6e41a545962cec97a7b78c6b86363ee1ec7a9f42699a5531'
      {
         "detail": "You don't have the permission to access the requested resource. It is either read-protected or not readable by the server.", 
         "instance": "about:blank", 
         "status": 403, 
         "title": "403 Forbidden: You don't have the permission to access the requested resource. It is either read-protected or not readable by the server.", 
         "type": "about:blank"
       }

#. Unknown sha512 should return invalid error (return code: 400)

   .. code-block:: console

       $ curl -X GET --header 'Accept: application/json' 'https://tooltool.mozilla-releng.net/sha512/invalid'
       {
         "detail": "Invalid sha512 digest", 
         "instance": "about:blank", 
         "status": 400, 
         "title": "400 Bad Request: Invalid sha512 digest", 
         "type": "about:blank"
       }


.. _`Rok Garbas`: https://phonebook.mozilla.org/?search/Rok%20Garbas
.. _`Release Engineering`: https://wiki.mozilla.org/ReleaseEngineering#Contacting_Release_Engineering
