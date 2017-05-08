Deploying
=========

Deployment happens **automatically** in :ref:`continuous integration
<continuous-integration>` when code is pushed / merged to **staging** or
**production** branch.

If interested please read more on :ref:`branching policy <branching-policy>`.


Release Schedule
----------------

Releases happen on a **weekly** basis, on Wednesday, excluding `Firefox release
weeks`_ and chemspill weeks.

`Next release`_ is announced in github issue tracker.

Any **out-of-schedule** release can be requested by contacting :ref:`Services
manager <services-managers>` or `creating a ticket on github`_.

.. _`Firefox release weeks`: https://wiki.mozilla.org/RapidRelease/Calendar
.. _`creating a ticket on github`: https://github.com/mozilla-releng/services/issues/new
.. _`Next release`: https://github.com/mozilla-releng/services/issues?q=is%3Aopen+is%3Apr+label%3A%220.kind%3A+release%22


Release Protocol
----------------

This protocal is followed by the :ref:`services manager <services-managers>`.

#. If not already there, create a PR from ``master`` to ``production`` branch.
   (`Example of release PR`_).

   Please make sure that release notes are collected in description of the PR.
   Encurage developers adding release notes as their PR gets merged into
   ``master``.

#. A day prior to the scheduled release send an email to all :ref:`service
   owners <service-owners>`

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

       We encurage everybody that contributed to this release to join "#shipit" channel where release is going to be coordinated. 

       Please follow the link bellow for more details.

           <LINK-TO-RELEASE-PR>

       For any question please contact

           <CURRENT-RELEASE-MANAGER>

       Thank you!


#. Before starting a release inform MOC person on duty (in ``#moc`` channel)
   that new deployment of ``mozilla-releng/services`` is going to be happen.
   The channel subject should contain `on duty sysadmin:` followed by the IRC
   nickname to contact.
   
   If some monitoring alert goes off then kindly ask to ping you directly - the
   services manager.

   Example message::

       nickname: I am about to release a new version of mozilla-releng/services (*.mozilla-releng.net). Any alerts coming up soon will be best directed to me. I'll let you know when it's all done. Thank you!

#. Release starts by :ref:`services manager <services-managers>` logging all the
   steps into ``#shipit`` channel and coordinating with others.

#. Push to ``staging`` branch and do - if needed - some manual checks.

   .. code-block:: console

        $ git clone git@github.com:mozilla-releng/services.git
        $ cd services
        $ git checkout -b staging origin/staging
        $ git push origin staging -f 

#. Verify the staging sites are functioning properly.

   #. `Staging Site`_
   #. `Treestatus Staging`_
   #. `Shipit Staging`_
   #. `Shipit Staging Dashboard`_

   Monitor the `Heroku dashboard`_ for errors.

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

#. Verify the production sites are functioning properly.

   - `Main Site`_
   - `Treestatus`_
   - `Shipit`_
   - `Shipit Dashboard`_

   Monitor the `Heroku dashboard`_ for errors

#. Fill in the release notes on GitHub

   `New GitHub Release`_

   If the previous release was done on 2017/05/04 then a good starting point might be

   .. code-block:: console

       git shortlog --since="20170504" | sed -e '/^[^ ]/d' -e '/^$/d' -e 's/^[ \t]*/- /g' | sor


#. Bump version in master

   .. code-block:: console
   
        $ git clone git@github.com/mozilla-releng/services.git
        $ cd services
        $ echo "$((($(cat VERSION)) + 1))" | tee VERSION2
        $ mv VERSION2 VERSION
        $ git commit VERSION -m "setup: bumping to v$(cat ./VERSION)"
        $ git push origin master


#. `Open next release PR`_ The title should be `Release: vNN` where `NN` is the new version number.

#. Notify MOC person on duty (in ``#moc`` channel) that release is done.

#. Send email to `Release Engineering`_ and `Release Management`_ Team
   announcing that new release just happened.

   Email subject::

       mozilla-releng/services v<VERSION> was released

   Email body::

       Hi,

       If you are not interested in work being done in mozilla-releng/services[1] you can stop reading this email.

       ------

       mozilla-releng/services[1] is a common platform to develop, test and deploy different parts of our release pipeline. The purpose of this email is to inform every team contributing to mozilla-releng/services what was released to avoid unexpected situations.


       ### Notable changes in v<VERSION>

       <WRITE-HIGHLIGHTS-OF-THE-RELEASE>
         Include links to
           (1) release PR,
           (2) release notes and
           (3) irc logs
         Also comment on a release, eg: what went good, what not so good
         and what should we improve in future.
         You might also pick few (eg. 2-3) good-first-bugs and ask for some
         help.
       </WRITE-HIGHLIGHTS-OF-THE-RELEASE>


       ### Next release

       Next release is going to be on
       
           <NEXT_RELEASE_DATETIME>
           Release date and time in multiple timezones.
           Example:
           2017-04-27 11:00 UTC
           2017-04-27 04:00 PDT  (UTC-7)
           2017-04-27 07:00 EDT  (UTC-4)
           2017-04-27 13:00 CEST (UTC+2)
           </NEXT_RELEASE_DATETIME>

       and is going to be managed by
           <NEXT-RELEASE-MANAGER>
             provide link to phonebook for contacting details
           </NEXT-RELEASE-MANAGER>
       
       You can follow the progress for next release in a release PR:
           <LINK-TO-NEXT-RELEASE-PR>


       Thank you!


       [1] https://github.com/mozilla-releng/services


.. _`Example of release PR`: https://github.com/mozilla-releng/services/pull/237
.. _`Open next release PR`: https://github.com/mozilla-releng/services/compare/production...master
.. _`Release Engineering`: https://wiki.mozilla.org/ReleaseEngineering
.. _`Release Management`: https://wiki.mozilla.org/Release_Management
.. _`Staging Site`: https://treestatus.staging.mozilla-releng.net/
.. _`Treestatus Staging`: https://staging.mozilla-releng.net/
.. _`Shipit Staging`: https://shipit.staging.mozilla-releng.net/
.. _`Shipit Staging Dashboard`: https://dashboard.shipit.staging.mozilla-releng.net/
.. _`Main Site`: https://treestatus.mozilla-releng.net/
.. _`Treestatus`: https://www.mozilla-releng.net/
.. _`Shipit`: https://shipit.mozilla-releng.net/
.. _`Shipit Dashboard`: https://dashboard.shipit.mozilla-releng.net/
.. _`Heroku dashboard`: https://dashboard.heroku.com/apps/releng-production-treestatus/metrics/web
.. _`New GitHub Release`: https://github.com/mozilla-releng/services/releases/new

.. _services-managers:

Services Managers
-----------------

- `Rok Garbas`_


.. _service-owners:

Service Owners
--------------

+--------------------------------+---------------------------+
+ Service                        | Owner(s)                  |
+================================+===========================+
+ :ref:`releng_archiver`         | - `Rok Garbas`_           |
+--------------------------------+---------------------------+
+ :ref:`releng_clobberer`        | - `Rok Garbas`_           |
+--------------------------------+---------------------------+
+ :ref:`releng_docs`             | - `Rok Garbas`_           |
+--------------------------------+---------------------------+
+ :ref:`releng_frontend`         | - `Rok Garbas`_           |
+--------------------------------+---------------------------+
+ :ref:`releng_mapper`           | - `Rok Garbas`_           |
+--------------------------------+---------------------------+
+ :ref:`releng_slavehealth`      | - `Rok Garbas`_           |
+--------------------------------+---------------------------+
+ :ref:`releng_tooltool`         | - `Rok Garbas`_           |
+--------------------------------+---------------------------+
+ :ref:`releng_treestatus`       | - `Rok Garbas`_           |
+--------------------------------+---------------------------+
+ :ref:`shipit_bot_uplift`       | - `Bastien Abadie`_       |
+--------------------------------+---------------------------+
+ :ref:`shipit_code_coverage`    + - `Bastien Abadie`_       +
+                                | - `Marco Castelluccio`_   |
+--------------------------------+---------------------------+
+ :ref:`shipit_frontend`         | - `Rok Garbas`_           |
+                                | - `Bastien Abadie`_       |
+--------------------------------+---------------------------+
+ :ref:`shipit_pipeline`         | - (not yet started)       |
+--------------------------------+---------------------------+
+ :ref:`shipit_pulse_listener`   + - `Bastien Abadie`_       +
+                                | - `Marco Castelluccio`_   |
+--------------------------------+---------------------------+
+ :ref:`shipit_risk_assessment`  + - `Bastien Abadie`_       +
+                                | - `Marco Castelluccio`_   |
+--------------------------------+---------------------------+
+ :ref:`shipit_signoff`          | - `Ben Hearsum`_          |
+                                | - `Simon Fraser`_         |
+--------------------------------+---------------------------+
+ :ref:`shipit_static_analysis`  + - `Bastien Abadie`_       +
+                                | - `Marco Castelluccio`_   |
+--------------------------------+---------------------------+
+ :ref:`shipit_uplift`           | - `Bastien Abadie`_       |
+                                | - `Marco Castelluccio`_   |
+--------------------------------+---------------------------+
+ :ref:`shipit_taskcluster`      | - `Jordan Lund`_          |
+                                | - `Nick Thomas`_          |
+--------------------------------+---------------------------+


In case when Owner(s) of services are on PTO or not responsive please follow
`Contacting Release Engineering`_ wiki page.


.. _`Rok Garbas`: https://phonebook.mozilla.org/?search/Rok%20Garbas
.. _`Ben Hearsum`: https://phonebook.mozilla.org/?search/Ben%20Hearsum
.. _`Simon Fraser`: https://phonebook.mozilla.org/?search/Simon%20Fraser
.. _`Jordan Lund`: https://phonebook.mozilla.org/?search/Jordan%20Lund
.. _`Nick Thomas`: https://phonebook.mozilla.org/?search/Nick%20Thomas
.. _`Marco Castelluccio`: https://phonebook.mozilla.org/?search/Marco%20Castelluccio
.. _`Bastien Abadie`: https://github.com/La0
.. _`Contacting Release Engineering`: https://wiki.mozilla.org/ReleaseEngineering#Contacting_Release_Engineering


.. _continuous-integration:

Continuos Integration
---------------------

TODO: write about taskcluster github integration


Deployment targets
------------------

TODO: where can we deploy

- amazon s3
- amazon aws (soon)
- heroku
- building docker
- via ssh

