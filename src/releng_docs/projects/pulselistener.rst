.. pulselistener-project:

Project: pulselistener
==============================

:contact: `Bastien Abadie`_, (backup `Release Management`_)

This is a monitoring component that reacts to Pulse_ messages, like:

- `mozilla-central build`_ finished
- new MozReview_ review request submitted

It also polls for new things to do:

- new Phabricator_ differential submitted

When it has captured a new event, it triggers tasks:

- ``shipit_code_coverage``: triggered after builds finished, to gather and
  upload coverage data;
- ``shipit_static_analysis``: triggered on review requests, to provide linting
  and static analysis reports through a comment made by a bot.

This project is hosted on Heroku_, as a worker dyno. We use several instances
of this service for production, staging and testing.

The hooks
---------

The functionality described above is implemented in a few classes defined in
``shipit_code_coverage/listener.py``:

- ``HookPhabricator``: Taskcluster hook handling the static analysis for
  Phabricator differentials. This polls the Phabricator API (the
  ``differential.diff.search`` endpoint) every minute for new revisions.
- ``HookStaticAnalysis``: Taskcluster hook handling the static analysis for
  MozReview. This handles Pulse messages with route
  ``mozreview.commits.published`` by extracting the new commits from the
  message payload.
- ``HookCodeCoverage``: Taskcluster hook handling code coverage. This listens
  for ``task-group-resolved`` pulse messages and filters for `mozilla-central`
  code coverage build tasks. When one suitable task is found, it uses the
  hg.mozilla.org revision hash to trigger a code coverage upload task.

When these listeners run successfully, they will call back to Taskcluster to
create new tasks. As an example, see the `shipit code coverage production
hook`_ and `shipit static analysis production hook`_ on the Taskcluster Hooks
Manager.


.. _Bastien Abadie: https://github.com/La0
.. _Release Management: https://wiki.mozilla.org/Release_Management
.. _Pulse: https://wiki.mozilla.org/Auto-tools/Projects/Pulse
.. _Heroku: https://www.heroku.com/
.. _shipit code coverage production hook: https://tools.taskcluster.net/hooks/project-releng/services-production-codecoverage
.. _shipit static analysis production hook: https://tools.taskcluster.net/hooks/project-releng/services-production-shipit-static-analysis
.. _mozilla-central build: https://treeherder.mozilla.org/#/jobs?repo=mozilla-central
.. _Phabricator: https://phabricator.services.mozilla.com/
.. _MozReview: https://reviewboard.mozilla.org/
