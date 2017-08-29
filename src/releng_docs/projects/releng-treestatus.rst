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
:database (postresql):
  `production <https://data.heroku.com/datastores/dad34d86-54d0-46fc-911e-82768c73f247>`_,
  `staging <https://data.heroku.com/datastores/81feab6a-0a7c-4489-a6a1-9c0106c5e0ea>`_
:cache (redis):
  `poroduction <https://data.heroku.com/datastores/04b0b822-a806-475b-a397-38df291284fc>`_,
  `staging <https://data.heroku.com/datastores/6f5e3490-0e46-4e7b-89d1-abbfb1fd9026>`_
:contact: `Rok Garbas`_, (backup `Release Engineering`_)


TreeStatus is a relatively simple tool to keep track of the status of the
**trees** at Mozilla.

**A tree** is a version-control repository, and can generally be in one of
three states: **open**, **closed**, or **approval-required**. These states
affect the ability of developers to push new commits to these repositories.
Trees typically close when something prevents builds and tests from succeeding.

The tree status tool provides an interface for **anyone to see the current
status of all trees**. It also allows "sheriffs" to manipulate tree status.


Infrastructure
--------------

.. blockdiag::
    :align: center

    orientation = portrait

    A [ label = "https://mozilla-releng.net/treestatus\nproject: releng-frontend\n(AWS S3)"
      , width = 180
      , height = 60
      ];

    B [ label = "https://treestatus.mozilla-releng.net/\nproject: releng-treestatus\n(Heroku)"
      , width = 180
      , height = 60
      ];

    C [ label = "postgresql\n(Heroku)"
      , width = 180
      , height = 60
      ];

    A -> B -> C

Troubleshooting
---------------

#. Look at `Heroku metrics
   <https://dashboard.heroku.com/apps/releng-production-treestatus/metrics/web>`_
   to get birds view on the running application.

#. There might be some problems with Heroku. Make sure to also check their
   `status page <https://status.heroku.com>`_

#. Check if there is 

#. To see more logs (from past) look at Papertrails.

#. Sometimes restarting an application might solve the issue (at least
   temporary). Once you restart the application also verify that it is working
   correctly (follow :ref:`instructions below <verify-releng-treestatus>`).


Digging deeper
--------------

**To start developing** ``releng-treestatus`` please follow :ref:`development
guide <develop-flask-project>`.

**To (re)deploy** ``releng-treestatus`` to Heroku please follow
:ref:`deployment guide <deploy-heroku-target>`.

.. _verify-releng-treestatus:

**To test (verify)** that ``releng-treestatus`` is running correctly please
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

       $ curl -X GET --header 'Accept: application/json' '$URL/trees'
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

       $ curl -X GET --header 'Accept: application/json' '$URL/trees/mozilla-beta'
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

       $ curl -X GET --header 'Accept: application/json' '$URL/trees/invalid'
       {
         "detail": "No such tree",
         "instance": "about:blank",
         "status": 404,
         "title": "404 Not Found: No such tree",
         "type": "about:blank"
       }


.. _`Rok Garbas`: https://phonebook.mozilla.org/?search/Rok%20Garbas
.. _`Release Engineering`: https://wiki.mozilla.org/ReleaseEngineering#Contacting_Release_Engineering
