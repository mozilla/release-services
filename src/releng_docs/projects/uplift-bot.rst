.. _shipit-bot-uplift-project:

Project: uplift/bot
==========================


:production: https://tools.taskcluster.net/hooks/project-releng/services-production-shipit-bot-uplift
:staging: https://tools.taskcluster.net/hooks/project-releng/services-staging-shipit-bot-uplift
:contact: `Bastien Abadie`_, (backup `Release Engineering`_)

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

This secret holds the configuration for all the services, you can look at the ``uplift/bot`` section for more details.

2. Taskcluster client
"""""""""""""""""""""

You need to create a `Taskcluster client`_ to run the uplift bot task on your computer.

Use the form to create a new client in your own namespace (the ``ClientId`` should be pre-filled with ``mozilla-auth0/ad|Mozilla-LDAP|login/``, simply add an explicit suffix, like ``uplift-bot-dev``)

Add an explicit description, you can leave the ``Expires`` setting into the far future.

Add the Taskcluster scope needed to read the secret previously mentioned: ``secrets:get:repo:github.com/mozilla-releng/services:branch:master``

To summarize, you need to setup your client (if your login is ``bastien``), like this:

============= ====================================================================
Key           Value
============= ====================================================================
ClientId      ``mozilla-auth0/ad|Mozilla-LDAP|XXX``
Description   My own uplift bot development client
Client Scopes ``secrets:get:repo:github.com/mozilla-releng/services:branch:master``
============= ====================================================================


.. warning::
  Save the **access token** provided by Taskcluster after creating your client, it won't be displayed afterwards


3. Project shell
""""""""""""""""

To work, uplift bot needs ``postgresql``, ``uplift/backend`` and ``uplift/bot``.

Run the following commands (where ``XXX`` is the Taskcluster access token) in separate terminals:

.. code-block:: shell

  ./please run postgresql
  ./please run uplift/backend \
    --taskcluster-client-id="mozilla-auth0/ad|Mozilla-LDAP|XXX" \
    --taskcluster-access-token=XXX
  ./please shell uplift/bot \
    --taskcluster-client-id="mozilla-auth0/ad|Mozilla-LDAP|XXX" \
    --taskcluster-access-token=XXX

Once the initial build finishes and all the dependencies are started, you should get a green Nix shell, running in ``/app/src/uplift/bot``.


4. Run the bot
""""""""""""""

You can run the bot with this command (in the Nix Shell):

.. code-block:: shell

  mkdir -p /tmp/shipit_bot_cache
  uplift-bot

  # If you have issues with permissions or python setup in nix
  export PYTHONPATH="/app/src/uplift/bot:$PYTHONPATH"
  python uplift_bot/cli.py

You can also run the bot on a particular bug (e.g. Bug 123456) like so:

.. code-block:: shell

  uplift-bot 123456

.. _libmozdata: https://github.com/mozilla/libmozdata/
.. _`Bastien Abadie`: https://github.com/La0
.. _`Release Engineering`: https://wiki.mozilla.org/ReleaseEngineering#Contacting_Release_Engineering
.. _`Taskcluster`: https://tools.taskcluster.net/
.. _`Taskcluster client`: https://tools.taskcluster.net/auth/clients
