.. _deploy-regular:

Regular releases
================

Push to production happens in regular batches. Usually every second week,
starting on Wednesday (testing on staging) and final deployment to production
on Thursday.

.. _deploy-release-managers:

Current administrators that perform regular releases are:

- `Rok Garbas`_
- `Bastien Abadie`_
- `Rail Aliiev`_
- `Jan Keromnes`_

Release schedule is published in `Release Services calendar`_.

.. _`Rok Garbas`: https://phonebook.mozilla.org/?search/Rok%20Garbas
.. _`Bastien Abadie`: https://phonebook.mozilla.org/?search/Bastien%20Abadie
.. _`Rail Aliiev`: https://phonebook.mozilla.org/?search/Rail%20Aliiev
.. _`Jan Keromnes`: https://phonebook.mozilla.org/?search/Jan%20Keromnes
.. _`Release Services calendar`: https://calendar.google.com/calendar/embed?src=mozilla.com_sq62ki4vs3cgpclvkdbhe3rgic%40group.calendar.google.com

Protocol that we follow is:


1. Push to staging branch
-------------------------

Prior to release a push to ``staging`` branch must happen. This will
trigger a deploy of all projects to staging environments.

.. code-block:: console

     $ git clone git@github.com:mozilla/release-services.git
     $ cd release-services
     $ git push -f origin origin/master:staging


2. Verify projects on production
--------------------------------

Verify that all the production projects in staging that they are functioning
properly. Each project should have a list of steps that you can easily
verify that a deployment was sucessful.

 .. todo:: ref to list of production projects.
 .
Example: :ref:`verify tooltool/api project <verify-tooltool-api>`

Only proceed further once production projects work in staging environment.

.. todo:: explain that some projects are only enabled on staging, but you
          only need to check projects which are enabled on production.

  
3. Announce new deployment
--------------------------

Announce that new deployment to production is going to happen

- announce in ``#ci`` channel that a push to production is about to
  happen.

  Example message::

      I am about to release a new version of mozilla/release-services
      (*.mozilla-releng.net, *.moz.tools). Any alerts coming up soon will be
      best directed to me. I'll let you know when it's all done. Thank you!

- inform MOC person on duty (in ``#moc`` channel) that new deployment of
  ``mozilla/release-services`` is going to be happen. The channel subject
  should contain ``on duty sysadmin:`` followed by the IRC nickname you need
  to contact.

  Example message::

      nickname: I am about to release a new version of
      mozilla/release-services (*.mozilla-releng.net, *.moz.tools). Any
      alerts coming up soon will be best directed to me. I'll let you know
      when it's all done. Thank you!


4. Start production deployment
------------------------------

Push to ``production``. Create a merge commit of master branch and tag it.
Don't forget to push just created tag.

.. code-block:: console

    $ git clone git@github.com/mozilla/release-services.git
    $ cd release-services
    $ git checkout -b production origin/production
    $ git merge master -m "Release: v$(git show master:VERSION)"
    $ git push origin production
    $ git tag v$(cat ./VERSION)
    $ git push origin v$(cat ./VERSION)


5. Verify projects on production
--------------------------------

Verify that all production projects are now deployed and working properly in
production environment. Use the same checks as we did before when we were
checking if projects are working on staging, but now use production URLs.

Example: :ref:`verify tooltool/api project <verify-tooltool-api>`

.. todo:: need to explain how to revert when a deployment goes bad.


6. Write release notes
----------------------

Fill in the release notes on GitHub

`New GitHub Release`_

If the previous release was done on 2017/05/04 then a good starting point might be

.. code-block:: console

    $ git log --oneline v$((($(cat VERSION)) - 1)).. HEAD \
        | cut -d' ' -f2- \
        | sort \
        | grep -v 'setup: bumping to'


7. Bump version
---------------

**DO NOT** push upstream just yet.

.. code-block:: console

    $ git clone git@github.com/mozilla/release-services.git
    $ cd release-services
    $ echo "$((($(cat VERSION)) + 1))" | tee VERSION2
    $ sed -i -e "s|base-$(cat VERSION)|base-$(cat VERSION2)|" .taskcluster.yml
    $ mv VERSION2 VERSION


8. Push new base image for new version
--------------------------------------

.. code-block:: console

    $ ./please -vv tools base-image \
         --taskcluster-client-id="..." \
         --taskcluster-access-token="..."

Docker username and password you get in `staging secrets`_ or `production
secrets`_ secrets.

It might happen that push to docker hub will fail since the resulting docker
image is quite big (~1.5GB). When it fails you can only retrigger the
``docker push`` command.

.. code-block:: console

    $ docker push mozillareleng/services:base-$(cat ./VERSION)


9. Commit the version bump
--------------------------

Once base image is pushed to docker hub, commit the version bump and push it
to upstream repository.

.. code-block:: console

    $ git commit VERSION .taskcluster.yml -m "setup: bumping to v$(cat ./VERSION)"
    $ git push origin master

Make sure that commit gets properly build before proceeding. This will
ensure that docker base image created in previous steps is working.


10. Announce that deployment to production is done
--------------------------------------------------

- announce in ``#ci`` channel that a push to production is complete.

  Example message::

      Previously annonced release of mozilla/release-services
      (*.mozilla-releng.net, *.moz.tools) to productions is now complete. If
      you see anything behaving weird please let me know. Changes ->
      <link-to-release-notes>.

- inform MOC person on duty (in ``#moc`` channel) that deployment of
  ``mozilla/release-services`` is complete.

  Example message::

      nickname: Previously annonced release of mozilla/release-services
      (*.mozilla-releng.net, *.moz.tools) to productions is now complete.
      Changes -> <link-to-release-notes>.


.. _`Rok Garbas`: https://phonebook.mozilla.org/?search/Rok%20Garbas
.. _`Bastien Abadie`: https://phonebook.mozilla.org/?search/Bastien%20Abadie
.. _`Rail Aliiev`: https://phonebook.mozilla.org/?search/Rail%20Aliiev
.. _`New GitHub Release`: https://github.com/mozilla/release-services/releases/new
.. _`staging secrets`: https://tools.taskcluster.net/secrets/repo%3Agithub.com%2Fmozilla-releng%2Fservices%3Abranch%3Astaging
.. _`production secrets`: https://tools.taskcluster.net/secrets/repo%3Agithub.com%2Fmozilla-releng%2Fservices%3Abranch%3Aproduction
