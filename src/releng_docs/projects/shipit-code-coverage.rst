.. shipit-code-coverage-project:

Project: shipit-code-coverage
==========================

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

The last feature, upload to coveralls.io and codecov.io, can only be verified after waiting for a new push on mozilla-central. After that happens, ``shipit-pulse-listener`` should trigger a ``shipit-code-coverage`` task which should result in a new report being uploaded to coveralls.io and codecov.io.
