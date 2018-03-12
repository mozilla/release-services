.. _deploy-weekly-releases:

Regular weekly releases
=======================

Push to production happen in weekly batches. Once a week (usually on Thursday)
a release happens.

.. _deploy-release-managers:

Current administrators that perform this weekly release are:

- `Rok Garbas`_
- `Bastien Abadie`_

Protocal that we follow is:


#. Prior to release a push to ``staging`` branch must happen. This will
   trigger a deploy of all projects to staging environments.

   .. code-block:: console

        $ git clone git@github.com:mozilla-releng/services.git
        $ cd services
        $ git checkout -b staging origin/staging
        $ git push origin staging -f 

#. Verify that all the production projects in staging that they are functioning
   properly. Each project should have a list of steps that you can easily
   verify that a deployment was sucessful.

    .. todo:: ref to list of production projects.
    .
   Example: :ref:`verify releng-tooltool project <verify-releng-tooltool>`

   Only proceed further once production projects work in staging environment.

   .. todo:: explain that some projects are only enabled on staging, but you
             only need to check projects which are enabled on production.

#. Announce that new deployment to production is going to happen

   - announce in ``#releng`` channel that a push to production is about to
     happen.

     Example message::

         I am about to release a new version of mozilla-releng/services (*.mozilla-releng.net). Any alerts coming up soon will be best directed to me. I'll let you know when it's all done. Thank you!

   - inform MOC person on duty (in ``#moc`` channel) that new deployment of
     ``mozilla-releng/services`` is going to be happen. The channel subject
     should contain ``on duty sysadmin:`` followed by the IRC nickname you need
     to contact.
   
     Example message::

         nickname: I am about to release a new version of mozilla-releng/services (*.mozilla-releng.net). Any alerts coming up soon will be best directed to me. I'll let you know when it's all done. Thank you!

#. Push to ``production``. Create a merge commit of master branch and tag it.
   Don't forget to push just created tag.

   .. code-block:: console

        $ git clone git@github.com/mozilla-releng/services.git
        $ cd services
        $ git checkout -b production origin/production
        $ git merge master -m "Release: v$(git show master:VERSION)"
        $ git push origin production
        $ git tag v$(cat ./VERSION)
        $ git push origin v$(cat ./VERSION)

#. Verify that all production projects are now deployed and working properly in
   production environment. Use the same checks as we did before when we were
   checking if projects are working on staging, but now use production URLs.

   Example: :ref:`verify releng-tooltool project <verify-releng-treestatus>`

   .. todo:: need to explain how to revert when a deployment goes bad.

#. Fill in the release notes on GitHub

   `New GitHub Release`_

   If the previous release was done on 2017/05/04 then a good starting point might be

   .. code-block:: console

       $ git log --oneline v$((($(cat VERSION)) - 1)).. HEAD \
           | cut -d' ' -f2- \
           | sort \
           | grep -v 'setup: bumping to'

#. Bump version, but **DO NOT** push upstream

   .. code-block:: console
   
        $ git clone git@github.com/mozilla-releng/services.git
        $ cd services
        $ echo "$((($(cat VERSION)) + 1))" | tee VERSION2
        $ sed -i -e "s|base-$(cat VERSION)|base-$(cat VERSION2)|" .taskcluster.yml
        $ mv VERSION2 VERSION

#. Push new base image for new version

   .. code-block:: console

        $ ./please -vv tools base-image \
            --docker-repo="mozillareleng/services" \
            --docker-tag="base-$(cat ./VERSION)" \
            --docker-username="..." \
            --docker-password="..."

   Docker username and password you get in `staging secrets`_ or `production
   secrets`_ secrets.

   It might happen that push to docker hub will fail since the resulting docker
   image is quite big (~1.5GB). When it fails you can only retrigger the
   ``docker push`` command.

   .. code-block:: console

       $ docker push mozillareleng/services:base-$(cat ./VERSION)

#. Once base image is pushed to docker hub, commit the version bump and push it
   to upstream repository.

   .. code-block:: console

        $ git commit VERSION .taskcluster.yml -m "setup: bumping to v$(cat ./VERSION)"
        $ git push origin master

    Make sure that commit gets properly build before proceeding. This will
    ensure that docker base image created in previous steps is working.

#. Announce that deployment to production is done.

   - announce in ``#releng`` channel that a push to production is complete.

     Example message::

         Previously annonced release of mozilla-releng/services (*.mozilla-releng.net) to productions is now complete. If you see anything behaving weird please let me know. Changes -> <link-to-release-notes>.

   - inform MOC person on duty (in ``#moc`` channel) that deployment of
     ``mozilla-releng/services`` is complete.

     Example message::

         nickname: Previously annonced release of mozilla-releng/services (*.mozilla-releng.net) to productions is now complete. Changes -> <link-to-release-notes>.


.. _`Rok Garbas`: https://phonebook.mozilla.org/?search/Rok%20Garbas
.. _`Bastien Abadie`: https://phonebook.mozilla.org/?search/Bastien%20Abadie
.. _`New GitHub Release`: https://github.com/mozilla-releng/services/releases/new
.. _`staging secrets`: https://tools.taskcluster.net/secrets/repo%3Agithub.com%2Fmozilla-releng%2Fservices%3Abranch%3Astaging
.. _`production secrets`: https://tools.taskcluster.net/secrets/repo%3Agithub.com%2Fmozilla-releng%2Fservices%3Abranch%3Aproduction
