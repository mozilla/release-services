.. _shipit-bot-uplift-project:

Project: shipit-bot-uplift
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


.. _libmozdata: https://github.com/mozilla/libmozdata/


.. _`Bastien Abadie`: https://github.com/La0
.. _`Release Engineering`: https://wiki.mozilla.org/ReleaseEngineering#Contacting_Release_Engineering
