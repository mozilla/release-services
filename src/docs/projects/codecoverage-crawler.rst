.. codecoverage-crawler:

Project: codecoverage/crawler
=============================

:contact: `Marco Castelluccio`_, (backup `Release Management`_)

This project uses the `Code Coverage Crawler`_ to browse pages from a list of
websites and publishes reports of code that is exercised by interacting with
those pages, but not exercised by our automated tests.

First, a code coverage build of Firefox is downloaded from Taskcluster, along
with code coverage artifacts that resulted from running the automated tests.
This is done using `firefox-code-coverage`_. The downloaded Firefox build is
used to navigate a list of websites, generating coverage data on the way. The
coverage data resulting from browsing websites is compared with the data
resulting from running the automated tests, and a report of these differences
is generated using genhtml_.

.. _Marco Castelluccio: https://github.com/marco-c
.. _Release Management: https://wiki.mozilla.org/Release_Management
.. _Code Coverage Crawler: https://github.com/mozilla/coverage-crawler
.. _firefox-code-coverage: https://github.com/marco-c/firefox-code-coverage
.. _genhtml: https://github.com/linux-test-project/lcov/blob/master/bin/genhtml
