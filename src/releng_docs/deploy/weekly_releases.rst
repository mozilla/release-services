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


#. A day prior to release a push to ``staging`` branch must happen. This will
   trigger a deploy of all projects to staging environments.

   .. code-block:: console

        $ git clone git@github.com:mozilla-releng/services.git
        $ cd services
        $ git checkout -b staging origin/staging
        $ git push origin staging -f 

#. Verify the production project in staging that they are functioning properly.
   Each project should have a list of steps that you can easily verify that
   a deployment was sucessful.

   Example: :ref:`verify releng-tooltool project <verify-releng-treestatus>`

#. Once a everything works on staging an email to ??? (relevant places) should
   be send announcing changes and when final release actually happens.

   This email should announce and remind everybody that release is going to
   happen to avoid surprises.
   
   Email subject::

       mozilla-releng/services release v<VERSION> is going to happen on
       <RELEASE_DATETIME_WITH_TIMEZONE>

   Email body::

       Hi,

       Next planned mozilla-releng/services relase is going to happen tomorrow.
       
       <RELEASE_DATETIME>
         Release date and time in multiple timezones.
         Example:
           2017-04-27 11:00 UTC
           2017-04-27 04:00 PDT  (UTC-7)
           2017-04-27 07:00 EDT  (UTC-4)
           2017-04-27 13:00 CEST (UTC+2)
       </RELEASE_DATETIME>

       We encurage everybody that contributed to this release to join "#shipit"
       channel where release is going to be coordinated. 

       Please follow the link bellow for more details.

           <LINK-TO-RELEASE-PR>

       For any question please contact

           <CURRENT-RELEASE-MANAGER>

       Thank you!


#. Before starting a release to production we inform MOC person on duty (in
   ``#moc`` channel) that new deployment of ``mozilla-releng/services`` is
   going to be happen.  The channel subject should contain ``on duty
   sysadmin:`` followed by the IRC nickname to contact.
   
   If some monitoring alert goes off then kindly ask to ping you directly.

   Example message::

       nickname: I am about to release a new version of mozilla-releng/services (*.mozilla-releng.net). Any alerts coming up soon will be best directed to me. I'll let you know when it's all done. Thank you!


#. Push to ``production`` branch and do (if needed) some manual checks.
   
   Create a merge comming (Example of merge commit) of master branch and tag it.

   .. code-block:: console

        $ git clone git@github.com/mozilla-releng/services.git
        $ cd services
        $ git checkout -b production origin/production
        $ git merge master -m "Release: v$(git show master:VERSION)"
        $ git push origin production
        $ git tag v$(cat ./VERSION)
        $ git push origin v$(cat ./VERSION)

#. Verify that all projects are now deployed and working properly in production
   environment. Use the same checks as we did before when we were checking if
   projects are working on staging.

   Example: :ref:`verify releng-tooltool project <verify-releng-treestatus>`

#. Bump version in master

   .. code-block:: console
   
        $ git clone git@github.com/mozilla-releng/services.git
        $ cd services
        $ echo "$((($(cat VERSION)) + 1))" | tee VERSION2
        $ mv VERSION2 VERSION
        $ git commit VERSION -m "setup: bumping to v$(cat ./VERSION)"
        $ git push origin master

#. Fill in the release notes on GitHub

   `New GitHub Release`_

   If the previous release was done on 2017/05/04 then a good starting point might be

   .. code-block:: console

       $ git log --oneline v$((($(cat VERSION)) - 1)).. HEAD \
           | cut -d' ' -f2- \
           | sort \
           | grep -v 'setup: bumping to'


#. Notify MOC person on duty (in ``#moc`` channel) that release is done.

#. Reply on announcement email that the release was done.


.. _`Rok Garbas`: https://phonebook.mozilla.org/?search/Rok%20Garbas
.. _`Bastien Abadie`: https://github.com/La0
.. _`New GitHub Release`: https://github.com/mozilla-releng/services/releases/new
