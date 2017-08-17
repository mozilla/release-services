.. _releng-treestatus-project:

Project: releng-treestatus
==========================


:url:
  `production <https://treestatus.mozilla-releng.net>`_, 
  `staging <https://treestatus.staging.mozilla-releng.net>`_
:papertrails:
  `production <https://papertrailapp.com/groups/4472992/events?q=program%3Amozilla-releng%2Fservices%2Fproduction%2Freleng-treestatus>`_,
  `staging <https://papertrailapp.com/groups/4472992/events?q=program%3Amozilla-releng%2Fservices%2Fstaging%2Freleng-treestatus>`_
:sentry:
  `production <https://sentry.prod.mozaws.net/operations/mozilla-releng-services/?query=environment%3Aproduction+site%3Areleng-treestatus+>`_,
  `staging <https://sentry.prod.mozaws.net/operations/mozilla-releng-services/?query=environment%3Astaging+site%3Areleng-treestatus+>`_
:heroku:
  `production <https://dashboard.heroku.com/apps/releng-production-treestatus>`_,
  `staging <https://dashboard.heroku.com/apps/releng-staging-treestatus>`_
:contact: `Rok Garbas`_, (backup `Release Engineering`_)


TreeStatus is a relatively simple tool to keep track of the status of the
**trees** at Mozilla.

**A tree** is a version-control repository, and can generally be in one of
three states: **open**, **closed**, or **approval-required**. These states
affect the ability of developers to push new commits to these repositories.
Trees typically close when something prevents builds and tests from succeeding.

The tree status tool provides an interface for **anyone to see the current
status of all trees**. It also allows "sheriffs" to manipulate tree status.


**To start developing** ``releng-treestatus`` please follow :ref:`development guide
<develop-flask-project>`.

**To (re)deploy** ``releng-treestatus`` to Heroku please follow :ref:`deployment
guide <deploy-heroku-target>`.

.. _verify-releng-treestatus:

**To test (verify)** that ``releng-treestatus`` is running correctly please follow the
following steps:

#. List all trees

   .. code-block:: console

       $ curl -X GET --header 'Accept: application/json' 'https://treestatus.mozilla-releng.net/trees'
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

       $ curl -X GET --header 'Accept: application/json' 'https://treestatus.mozilla-releng.net/trees/mozilla-beta'
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

       $ curl -X GET --header 'Accept: application/json' 'https://treestatus.mozilla-releng.net/trees/invalid'
       {
         "detail": "No such tree",
         "instance": "about:blank",
         "status": 404,
         "title": "404 Not Found: No such tree",
         "type": "about:blank"
       }


.. _`Rok Garbas`: https://phonebook.mozilla.org/?search/Rok%20Garbas
.. _`Release Engineering`: https://wiki.mozilla.org/ReleaseEngineering#Contacting_Release_Engineering
