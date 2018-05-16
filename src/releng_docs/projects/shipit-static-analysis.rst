.. _shipit-static-analysis-project:

Project: shipit-static-analysis
===============================

:contact: `Bastien Abadie`_, (backup `Release Management`_)

ShipIt static analysis is a Taskcluster task, triggered by *Shipit Pulse Listener* on every Mozreview or Phabricator new patch.
The task applies several code analyzers on each patch:

 * clang-tidy through ./mach static-analysis
 * clang-format through ./mach static-analysis
 * ./mach lint (mozlint)

And reports the results throug several channels:

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

This secret holds the configuration for all the services, you can look at the ``shipit-static-analysis`` section for more details.

2. Taskcluster client
"""""""""""""""""""""

You need to create a `Taskcluster client`_ to run the Static analysis task on your computer.

Use the form to create a new client in your own namespace (the ``ClientId`` should be pre-filled with ``mozilla-auth0/ad|Mozilla-LDAP|login/``, simply add an explicit suffix, like ``static-analysis-dev``)

Add an explicit description, you can leave the ``Expires`` setting into the far future.

Add the Taskcluster scope needed to read the secret previously mentionned: ``secrets:get:repo:github.com/mozilla-releng/services:branch:master``

To summarize, you need to setup your client (if your login is `bastien`), like this:

============= ====================================================================
Key           Value
============= ====================================================================
ClientId      ``mozilla-auth0/ad|Mozilla-LDAP|bastien/static-analysis-dev``
Description   My own Static analysis dev. client
Client Scopes ``secrets:get:repo:github.com/mozilla-releng/services:branch:master``
============= ====================================================================


.. warning::
  Save the **access token** provided by Taskcluster after creating your client, it won't be displayed afterwards


3. Project shell
""""""""""""""""

Run the following (where ``XXX`` is the Taskcluster access token):

.. code-block:: shell

  ./please shell shipit-static-analysis \
    --taskcluster-client-id=mozilla-auth0/ad|Mozilla-LDAP|bastien/static-analysis-dev \
    --taskcluster-access-token=XXX

Once the initial build finishes, you should get a green Nix shell, running in ``/app/src/shipit_static_analysis``.

4. Setup a Mozreview test
"""""""""""""""""""""""""

The bot needs an environment variable ``MOZREVIEW`` with the following informations:

* the Mozreview mercurial revision of the patch to analyze (named ``<HG_SHA>`` here),
* the Mozreview Review ID (named ``<MOZREVIEW_ID>`` here), 
* the Mozreview Diff ID (named ``<MOZREVIEW_DIFF>`` here).

So you'll need to do the following in the nix shell:

.. code-block:: shell
  
  export MOZREVIEW="<HG_SHA>:<MOZREVIEW_ID>:<MOZREVIEW_DIFF>"

Here is an example with this `Mozreview <https://reviewboard.mozilla.org/r/164530/>`_:

1. You can get ``<MOZREVIEW_ID>`` straight from the url (``164530`` here)
2. The Mercurial hash is in the first code sample (``hg pull -r ...``, so ``<HG_SHA>`` is : ``308c22e7899048467002de4ffb126cac0875c994``)
3. To get the ``<MOZREVIEW_DIFF>``, click on the Diff tab, then you'll see the last diff of this patch (here this diff 7)

So the command would be:

.. code-block:: shell
  
  export MOZREVIEW="308c22e7899048467002de4ffb126cac0875c994:164530:7"



5. Setup a Phabricator test
"""""""""""""""""""""""""""


6. Run the bot
""""""""""""""

Finally, you can run the bot with this command (in the Nix Shell):

.. code-block:: shell

  shipit-static-analysis \
    --taskcluster-secret=repo:github.com/mozilla-releng/services:branch:master \
    --cache-root=/app/tmp


.. _`Bastien Abadie`: https://github.com/La0
.. _`Release Management`: https://wiki.mozilla.org/Release_Management
.. _`Taskcluster`: https://tools.taskcluster.net/
.. _`Taskcluster client`: https://tools.taskcluster.net/auth/clients

