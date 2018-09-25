.. _staticanalysis/bot-project:

Project: staticanalysis/bot
===============================

:contact: `Bastien Abadie`_, (backup `Release Management`_)

Static analysis bot is a Taskcluster task, triggered by *Pulse Listener* on every new Mozreview or Phabricator patch.
The task applies several code analyzers on each patch:

 * clang-tidy through ./mach static-analysis
 * clang-format through ./mach static-analysis
 * ./mach lint (mozlint)

And reports the results through several channels:

 * emails,
 * MozReview comments,
 * Phabricator reviews.

Developer setup
---------------

0. Requirements
"""""""""""""""

You'll need:

1. A `Taskcluster`_ account
2. Docker

1. Taskcluster secret
"""""""""""""""""""""

Once logged on Taskcluster, please check that you can view the contents of the Taskcluster secret : `repo:github.com/mozilla-releng/services:branch:master <https://tools.taskcluster.net/secrets/repo%3Agithub.com%2Fmozilla-releng%2Fservices%3Abranch%3Amaster>`_.

This secret holds the configuration for all the services, you can look at the ``staticanalysis/bot`` section for more details.

If you need to make some changes to this secret, create a copy of this secret in your own namespace; and use its name everywhere the ``master`` secret is mentioned in this documentation.

2. Taskcluster client
"""""""""""""""""""""

You need to create a `Taskcluster client`_ to run the static analysis task on your computer.

Use the form to create a new client in your own namespace (the ``ClientId`` should be pre-filled with ``mozilla-auth0/ad|Mozilla-LDAP|login/``, simply add an explicit suffix, like ``static-analysis-dev``)

Add an explicit description, you can leave the ``Expires`` setting into the far future.

Add the Taskcluster scope needed to read the secret previously mentioned: ``secrets:get:repo:github.com/mozilla-releng/services:branch:master``

To summarize, you need to setup your client (if your login is ``bastien``), like this:

============= ====================================================================
Key           Value
============= ====================================================================
ClientId      ``mozilla-auth0/ad|Mozilla-LDAP|bastien/static-analysis-dev``
Description   My own static analysis dev. client
Client Scopes ``secrets:get:repo:github.com/mozilla-releng/services:branch:master``
============= ====================================================================


.. warning::
  Save the **access token** provided by Taskcluster after creating your client, it won't be displayed afterwards


3. Project shell
""""""""""""""""

Run the following (where ``XXX`` is the Taskcluster access token):

.. code-block:: shell

  ./please shell staticanalysis/bot \
    --taskcluster-client-id="mozilla-auth0/ad|Mozilla-LDAP|bastien/static-analysis-dev" \
    --taskcluster-access-token=XXX

Once the initial build finishes, you should get a green Nix shell, running in ``/app/src/staticanalysis/bot``.

4. Setup a Mozreview test
"""""""""""""""""""""""""

.. note::
  Make sure your Taskcluster secret has a ``mozreview`` reporter setup, as follows (with a valid ReviewBoard url, username and api_key):

  .. code-block:: yaml

    staticanalysis/bot:
      ...
      REPORTERS:
        - reporter: mozreview
          url: 'https://reviewboard.mozilla.org/'
          username: XXXX@mozilla.com
          api_key: YYYYY


The bot needs an environment variable ``MOZREVIEW`` with the following information:

* the Mozreview mercurial revision of the patch to analyze (named ``<HG_SHA>`` here),
* the Mozreview Review ID (named ``<MOZREVIEW_ID>`` here), 
* the Mozreview Diff ID (named ``<MOZREVIEW_DIFF>`` here).

So you'll need to do the following in the nix shell:

.. code-block:: shell
  
  export MOZREVIEW="<HG_SHA>:<MOZREVIEW_ID>:<MOZREVIEW_DIFF>"

Here is an example with this `Mozreview <https://reviewboard.mozilla.org/r/164530/>`_:

1. You can get ``<MOZREVIEW_ID>`` straight from the url (``164530`` here)
2. The Mercurial hash is in the first code sample (``hg pull -r ...``, so ``<HG_SHA>`` is : ``308c22e7899048467002de4ffb126cac0875c994``)
3. To get the ``<MOZREVIEW_DIFF>``, click on the Diff tab, then you'll see the last diff of this patch (in this case it is diff 7)

So the command would be:

.. code-block:: shell
  
  export MOZREVIEW="308c22e7899048467002de4ffb126cac0875c994:164530:7"



5. Setup a Phabricator test
"""""""""""""""""""""""""""


.. note::
  Make sure your Taskcluster secret has a ``phabricator`` reporter setup, as follows (with a valid Phabricator uri & token):

  .. code-block:: yaml

    staticanalysis/bot:
      ...
      REPORTERS:
        - reporter: phabricator
          url: 'https://phabricator-dev.allizom.org/api/'
          api_key: api-XXXX



The bot needs an environment variable ``PHABRICATOR`` containing the PHID of the diff to be reviewed.

So you'll need to do the following in the nix shell:

.. code-block:: shell
  
  export PHABRICATOR="<DIFF_PHID>"

Here is an example with this `Phabricator Diff review <https://phabricator-dev.allizom.org/D41>`_:

1. You can get the diff ID from the url (this is ``41``)
2. Login on the Phabricator instance (needed for API queries)
3. Go to the Conduit API web interface (``/conduit`` of the Phabricator instance), and click on the endpoint ``differential.query`` (direct link to `Phabricator DEV <https://phabricator-dev.allizom.org/conduit/method/differential.query/>`_)
4. Fill the form field ``ids`` as a JSON list of integer using the diff ID, so for our example : ``[41]``
5. Click ``Call Method``
6. The method result should have a ``activeDiffPHID`` key, that's our ``DIFF_PHID`` (in our example: ``PHID-DIFF-b5wsvctabxjmwqonwryv``)

Here is the final command line:

.. code-block:: shell
  
  export PHABRICATOR="PHID-DIFF-b5wsvctabxjmwqonwryv"


6. Run the bot
""""""""""""""

Finally, you can run the bot with this command (in the Nix Shell):

.. code-block:: shell

  mkdir -p /app/tmp
  staticanalysis/bot \
    --taskcluster-secret=repo:github.com/mozilla-releng/services:branch:master \
    --cache-root=/app/tmp


Is the static analysis project working correctly ?
--------------------------------------------------

During a release, the release manager needs to test if the static analyis is working on staging or production environment.

As the Taskcluster task is triggered by **pulselistener**, you need to login on the Heroku dashboard and see the logs of the pulse listener instances:

* `Pulse listener staging logs <https://dashboard.heroku.com/apps/shipit-staging-pulse-listener/logs>`_
* `Pulse listener production logs <https://dashboard.heroku.com/apps/shipit-production-pulse-listen/logs>`_

Once you see a log message ``Received new commits (commits=...)``, the following line should be ``Triggered a new task (id=XXXX)``

You can then check on the task status through `Taskcluster task inspector`_ (input the task id from log).

You'll be redirected to the task running (hopefully), and will see the logs. A static analysis task should always end up completed (even if issues are detected !).



.. _`Bastien Abadie`: https://github.com/La0
.. _`Release Management`: https://wiki.mozilla.org/Release_Management
.. _`Taskcluster`: https://tools.taskcluster.net/
.. _`Taskcluster client`: https://tools.taskcluster.net/auth/clients

.. _`Taskcluster task inspector`: https://tools.taskcluster.net/task-inspector
