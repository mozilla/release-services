.. _deploy-regular:

Regular deployment
==================

Regular production deployment of all projects happens once every two weeks.

.. _deploy-managers:

Administrators that perform this regular release are:

- `Rok Garbas`_
- `Bastien Abadie`_
- `Rail Aliiev`_
- `Jan Keromnes`_

Release schedule is published in `Release Services calendar`_. Protocol we follow is:

TODO: this should happen on Wed morning, point to the calendar

#. Push to staging channel.

   A day before pushing to production, on Wednesday morning, we push to
   projects to **staging channel**.

   To trigger automatic deployment to staging channel you need to force push
   from ``master`` to ``staging`` branch.

   .. code-block:: console

        $ git clone git@github.com:mozilla/release-services.git
        $ cd release-services
        $ git push -f origin origin/master:staging

   Once pushed to staging branch a deployment will start via taskcluster github
   integration. You can find a link to taskcluster deployment group at the
   `page listing commits of staging branch`_.

   .. image:: page_listing_commits_of_staging_branch.png

   To make everybody aware that this is happening announce staging deployment on
   `#release-services` IRC channel.::

      I'm pushed commit `<SHORT_SHA_OF_COMMIT>' to staging branch. Until
      tomorrow, when we deploy to production, staging branch is closed.
      Deployment to staging is happening here: `<LINK_TO_TASKCLUSTER>'.

   Now you need to close staging branch by checking **Protect this branch** via
   `staging settings page`_.

   .. image:: staging_settings_page.png

#. Testing projects on staging channel

   When deployment succeeds send email to ``release-services@mozilla.com``
   announcing that staging channel was successful and that maintainers need to
   test their projects.

   .. todo:: email template,  QA feedback need to be collected via email.
   .. todo:: how to list maintainers of projects?


#. Wednesday meeting

   .. todo:: go or no go decision

      are there any manual things we need to do
      when do we do a release? since maintainers need to be able to verify
    

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

   - announce in ``#ci`` channel that a push to production is about to
     happen.

     TODO: direct this to the person on duty

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

#. Push to ``production``. Create a merge commit of master branch and tag it.
   Don't forget to push just created tag.

  TODO: is this the correct branching model

   .. code-block:: console

       $ git clone git@github.com/mozilla/release-services.git
       $ cd release-services
       $ git checkout -b production origin/production
       $ git merge origin/master -m "Release: v$(git show origin/master:VERSION)"
       $ git push origin production
       $ git tag v$(cat ./VERSION)
       $ git push origin v$(cat ./VERSION)

TODO: release is in flight + link to taskcluster

#. Verify that all production projects are now deployed and working properly in
   production environment. Use the same checks as we did before when we were
   checking if projects are working on staging, but now use production URLs.

   Example: :ref:`verify releng-tooltool project <verify-releng-treestatus>`

   .. todo:: need to explain how to revert when a deployment goes bad.

TODO: we can already do this while waiting for the release to happen
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

       $ git clone git@github.com/mozilla/release-services.git
       $ cd release-services
       $ echo "$((($(cat VERSION)) + 1))" | tee VERSION2
       $ sed -i -e "s|base-$(cat VERSION)|base-$(cat VERSION2)|" .taskcluster.yml
       $ mv VERSION2 VERSION

#. Push new base image for new version

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

#. Once base image is pushed to docker hub, commit the version bump and push it
   to upstream repository.

   .. code-block:: console

       $ git commit VERSION .taskcluster.yml -m "setup: bumping to v$(cat ./VERSION)"
       $ git push origin master

   Make sure that commit gets properly build before proceeding. This will
   ensure that docker base image created in previous steps is working.

#. Announce that deployment to production is done.

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
.. _`Jan Keromnes`: https://phonebook.mozilla.org/?search/Jan%20Keromnes
.. _`New GitHub Release`: https://github.com/mozilla/release-services/releases/new
.. _`staging secrets`: https://tools.taskcluster.net/secrets/repo%3Agithub.com%2Fmozilla-releng%2Fservices%3Abranch%3Astaging
.. _`production secrets`: https://tools.taskcluster.net/secrets/repo%3Agithub.com%2Fmozilla-releng%2Fservices%3Abranch%3Aproduction
.. _`Release Services calendar`: https://calendar.google.com/calendar/embed?src=mozilla.com_sq62ki4vs3cgpclvkdbhe3rgic%40group.calendar.google.com
.. _`page listing commits of staging branch`: https://github.com/mozilla/release-services/commits/staging
.. _`staging settings page`: https://github.com/mozilla/release-services/settings/branches/staging
