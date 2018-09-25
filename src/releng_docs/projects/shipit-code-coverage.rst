.. shipit-code-coverage-project:

Project: shipit-code-coverage
==========================

:contact: `Marco Castelluccio`_, (backup `Release Management`_)

This project implements two things:

#. A task that runs on every ``mozilla-central`` push and uploads coverage
   reports to codecov.io_ and coveralls.io_.
#. A task that is run weekly and generates:

   - A report of files that are not covered by tests
     (``zero_coverage_report.json``). This report can be viewed at
     `code-coverage-reports`_. This is useful both at `detecting and removing
     dead code`_, and `figuring out where to add tests`_.
   - A file (``chunk_mapping.sqlite``) that maps:
      - from source files to test chunks that cover them,
      - from source files to tests that cover them,
      - from test chunks to the test files that they contain.
   - A coverage report of `web-platform-tests`, uploaded to `the
     code-coverage-reports GitHub repo`_ .

These artifacts can be obtained from the `taskcluster index`_.

.. _Marco Castelluccio: https://github.com/marco-c
.. _Release Management: https://wiki.mozilla.org/Release_Management
.. _codecov.io: https://codecov.io/gh/marco-c/gecko-dev
.. _coveralls.io: https://coveralls.io/github/marco-c/gecko-dev
.. _detecting and removing dead code: https://bugzilla.mozilla.org/show_bug.cgi?id=1415819
.. _figuring out where to add tests: https://bugzilla.mozilla.org/show_bug.cgi?id=1415824
.. _code-coverage-reports: https://marco-c.github.io/code-coverage-reports
.. _the code-coverage-reports GitHub repo: https://github.com/marco-c/code-coverage-reports/tree/master
.. _taskcluster index: https://tools.taskcluster.net/index/project.releng.services.project.production.shipit_code_coverage/latest

Is the code coverage project working correctly?
--------------------------------

.. _verify-shipit-code-coverage:

**To test and verify** that ``shipit-code-coverage`` is running correctly please
follow the following steps:

#. Trigger the shipit-code-coverage hook manually;

#. Check that there are no errors with the triggered tasks;

#. Verify the files ``chunk_mapping.tar.xz``, ``web-platform-tests.tar.xz``, ``zero_coverage_files.json`` are uploaded to `https://github.com/marco-c/code-coverage-reports <https://github.com/marco-c/code-coverage-reports>`_;

#. Verify `https://marco-c.github.io/code-coverage-reports/ <https://marco-c.github.io/code-coverage-reports/>`_ contains a reasonable number of files (usually > 8000).

Most of the features of the task can be checked with the steps above.

The last feature, upload to coveralls.io and codecov.io, can only be verified after waiting for a new push on mozilla-central. After that happens, ``pulselistener`` should trigger a ``shipit-code-coverage`` task which should result in a new report being uploaded to coveralls.io and codecov.io.
