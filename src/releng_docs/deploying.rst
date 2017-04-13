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
   
   Template for email::

       SUBJECT:

           mozilla-releng/services release v<VERSION> is going to
           happen on <RELEASE_DATETIME>

       BODY:

           Hi,

           Next planned mozilla-releng/services relase is going to
           happen tomorrow. We encurage everybody that contributed
           to this release to join "#shipit" channel where release
           is going to be coordinated. 

               YYYY-MM-DD MM:HH CET
               YYYY-MM-DD MM:HH PST

           Please follow the link bellow for more details.

               <LINK-TO-RELEASE-PR>

           For any question please contact

               <CURRENT-RELEASE-MANAGER>

          
#. Release starts by :ref:`services manager <services-managers>` logging all the
   steps into ``#shipit`` channel and coordinating with others.

#. Push to ``staging`` branch and do (if needed) some manual checks.

   .. code-block:: shell

        $ git clone git@github.com/mozilla-releng/services.git
        $ cd services
        $ git checkout -b staging origin/staging
        $ git push origin staging -f 

#. Push to ``production`` branch and do (if needed) some manual checks.
   
   Create a merge commig (Example of merge commit) of master branch and tag it

   .. code-block:: shell

        $ git clone git@github.com/mozilla-releng/services.git
        $ cd services
        $ git checkout -b production origin/production
        $ git merge master -m "Release: v`cat ./VERSION`"
        $ git push origin production
        $ git tag v`cat ./VERSION`
        $ git push origin v`cat ./VERSION`

#. Bump version in master

   .. code-block:: shell
   
        $ git clone git@github.com/mozilla-releng/services.git
        $ cd services
        $ rm -f VERSION
        $ echo "$(((`cat VERSION`) + 1))" > VERSION
        $ git commit VERSION -m "setup: bumping to `cat ./VERSION`"
        $ git push origin master


#. `Open next release PR`_

#. Send email to `Release Engineering`_ and `Release Management`_ Team
   announcing that new release just happened.

   Template for email::

       SUBJECT:

           mozilla-releng/services v<VERSION> was released

       BODY:

           Hi,

           mozilla-releng/services[1] is a common platform to
           develop, test and deploy different parts of our release
           pipeline.
           
           ------

           If you are not interested in work being done in
           mozilla-releng/services you can stop reading this
           email.

           ------

           Purpose of this email is to inform every team what
           was release and to be abore in case of any breakage.


           # Release notes for v<VERSION>

           <CONTENT-OF-RELEASE-PR>

           <LINK-TO-RELEASE-PR>


           # Next release

           Next release is going to be on
           
               YYYY-MM-DD MM:HH CET
               YYYY-MM-DD MM:HH PST

           and is going to be managed by
           
               <NEXT-RELEASE-MANAGER>
           
           You can follow the progress in release PR

               <LINK-TO-NEXT-RELEASE-PR>



           [1] https://github.com/mozilla-releng/services


.. _`Example of release PR`: https://github.com/mozilla-releng/services/pull/237
.. _`Open next release PR`: https://github.com/mozilla-releng/services/compare/production...master
.. _`Release Engineering`: https://wiki.mozilla.org/ReleaseEngineering
.. _`Release Management`: https://wiki.mozilla.org/Release_Management


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

