.. _staticanalysis/bot-project:

Project: staticanalysis/bot
===============================

:contact: `Bastien Abadie`_, (backup `Release Management`_)

Static Analysis bot is composed of a set of Taskcluster tasks, triggered by *Pulse Listener* on every new Phabricator patch, using a `HarborMaster build plan`_.

For each patch:

1. A try job is created in ``code-review`` mode
2. Analyzers described in the mozilla-central repository are run on the source code
3. Issues are reported are stored in a JSON file on each task, and reported as Taskcluster artifacts
4. Finally, a final task is triggered and uses this project to group all issues, filter them, and report them (email & Phabricator comments).

Developer setup
---------------

0. Requirements
"""""""""""""""

.. note::

  Static analysis bot is a pure Python project (no system dependencies). You can develop it without using Docker.

You'll need:

1. A `Taskcluster`_ account
2. *optional* Docker

1. Taskcluster secret
"""""""""""""""""""""

Once logged on Taskcluster, please check that you can view the contents of the Taskcluster secret : `repo:github.com/mozilla-releng/services:branch:master <https://tools.taskcluster.net/secrets/repo%3Agithub.com%2Fmozilla-releng%2Fservices%3Abranch%3Amaster>`_.

This secret holds the configuration for all the services, you can look at the ``staticanalysis/bot`` section for more details.

If you don't have access to that secret, or you need to make some changes to it, you can create a new secret under the "garbage" namespace (publicly visible to anyone); and use its name everywhere the ``master`` secret is mentioned in this documentation.

For example, you can create a secret called ``garbage/LOGIN/staticanalysis-bot-dev`` with this value:

.. code-block:: yaml

  common:
    APP_CHANNEL: master
  static-analysis-bot:
    PHABRICATOR:
      url: 'https://phabricator-dev.allizom.org/api/'
      api_key: api-YOURTOKEN
    REPORTERS:
      - reporter: mail
        emails:
          - YOUR@EMAIL.COM
      - reporter: phabricator

Just replace ``LOGIN`` with your username (e.g. ``michel``); ``api-YOURTOKEN`` with a new Conduit API Token from `Phabricator-dev`_ (hint: on Bugzilla-dev, you can just "Sign in with GitHub"); and ``YOUR@EMAIL.COM`` with your email address.

.. _`Phabricator-dev`: https://phabricator-dev.allizom.org/settings


2. Taskcluster authentication
"""""""""""""""""""""""""""""

You can simply use ``./please tools signin`` to create a new client on your Taskcluster account.

Once created, please add the required scope to read your secret: ``secrets:get:repo:github.com/mozilla-releng/services:branch:master`` (or ``secrets:get:garbage/michel/staticanalysis-bot-dev`` if you're using your own secret)

.. note:: 

  Your newly created credentials are stored in ``~/.config/please/config.toml``


3. Develop with Docker
""""""""""""""""""""""

Run the following:

.. code-block:: shell

  ./please shell staticanalysis/bot

Once the initial build finishes, you should get a green Nix shell, running in ``/app/src/staticanalysis/bot``.

.. code-block:: shell

  export TRY_TASK_ID="xxx"
  export TRY_TASK_GROUP_ID="yyy"
  export TASKCLUSTER_SECRET="path/to/your/secret"
  static-analysis-bot

4. Develop without Docker
"""""""""""""""""""""""""

It's possible to develop the project without using Docker.

.. warning::

  This is pretty experimental at this point, and you will encounter some pain points around Taskcluster integration.

You'll need to have `virtualenvwrapper <https://virtualenvwrapper.readthedocs.io/en/latest/>`_ installed on your computer.

On MacOSX, we presume that virtualenvwrapper will be installed in ``/usr/local/virtualenvwrapper.sh`` as a default instalation based on ``python3`` installed from ``brew`` as:

.. code-block:: shell

  pip install virtualenvwrapper
  source /usr/local/bin/virtualenvwrapper.sh

First, you need to create Python 3 virtual environment, and setup the project and its dependencies there:

.. code-block:: shell

  mkvirtualenv -p /usr/bin/python3 sa-bot

  # Setup mozilla-cli-common
  pip install -e lib/cli_common

  # Setup our bot
  pip install -r src/staticanalysis/bot/requirements_frozen.txt
  pip install -e src/staticanalysis/bot


Now you should be able to run succesfully the unit tests and lint tools:

.. code-block:: shell

  cd src/staticanalysis/bot
  pytest
  flake8

The project does not support reading your Taskcluster credentials without using ``please`` commands and Docker.

Here is a workaround to automatically use your credentials, by populating the necessary environment variables (I suggest writing these lines to a custom script...)

.. code-block:: shell

  export TASKCLUSTER_SECRET=path/to/your/secret
  export TASKCLUSTER_CLIENT_ID=$(grep 'taskcluster_client_id' ~/.config/please/config.toml | awk '{gsub(/"/, "", $3); print $3}')
  export TASKCLUSTER_ACCESS_TOKEN=$(grep 'taskcluster_access_token' ~/.config/please/config.toml | awk '{gsub(/"/, "", $3); print $3}')


Finally, you can run the project exactly like in the ``nix-shell`` above:

.. code-block:: shell

  export TRY_TASK_ID="xxx"
  export TRY_TASK_GROUP_ID="yyy"
  export TASKCLUSTER_SECRET="path/to/your/secret"
  static-analysis-bot

5. How to find a Taskcluster group to analyze
"""""""""""""""""""""""""""""""""""""""""""""

You need a valid Taskcluster group, with code review tasks to run the bot and configure the analysis with these 2 environment variables:

 * ``TRY_TASK_GROUP_ID`` is the Taskcluster Task Group ID with all the analysis
 * ``TRY_TASK_ID`` is the `code-review-issues`` Taskcluster Task ID in the above group

You can find all the analyses on Treeherder, using this `query (try + author=reviewbot) <https://treeherder.mozilla.org/#/jobs?repo=try&author=reviewbot>`_

By clicking on an analysis Taskcluster task, you'll be redirected to the group, and will be able to retrieve both ids.


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
.. _`HarborMaster build plan`: https://phabricator.services.mozilla.com/harbormaster/plan/4/

.. _`Taskcluster task inspector`: https://tools.taskcluster.net/task-inspector
