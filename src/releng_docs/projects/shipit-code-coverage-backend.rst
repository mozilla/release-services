.. shipit-code-coverage-backend-project:

Project: shipit-code-coverage-backend
=====================================

:production: https://coverage.moz.tools/docs/
:staging: https://coverage.staging.moz.tools/docs/
:contact: `Marco Castelluccio`_, (backup `Release Management`_)

This project offers a public-facing API to access code coverage information.
This project does not store data, instead it queries other services and
processes the results. These endpoints are being used by:

- the `Code Coverage Addon`_, a browser addon that injects code coverage
  information into pages like hg.mozilla.org_, dxr.mozilla.org_, searchfox.org_
  and Phabricator_;
- the `Firefox Code Coverage Frontend`_ that shows code coverage for code
  changed by patches.

.. _Marco Castelluccio: https://github.com/marco-c
.. _Release Management: https://wiki.mozilla.org/Release_Management
.. _Code Coverage Addon: https://github.com/mozilla/code-coverage-addon
.. _Firefox Code Coverage Frontend: https://github.com/mozilla/firefox-code-coverage-frontend
.. _hg.mozilla.org: https://hg.mozilla.org/mozilla-central/
.. _dxr.mozilla.org: https://dxr.mozilla.org/mozilla-central/source/
.. _searchfox.org: https://searchfox.org/mozilla-central/source/
.. _Phabricator: http://phabricator.services.mozilla.com/

The endpoints
-------------

The endpoints are described in ``shipit_code_coverage_backend/api.yml``. The
description and parameters for each endpoint are available through the Swagger
UI. Just visit the production_ or staging_ pages to see it.

There are two subsets of endpoints:

- The `legacy` endpoints hit external services like codecov.io_ and coveralls.io_. They are planned for removal.
- The `v2` endpoints only query `hg.mozilla.org` and ActiveData_.

.. _production: https://coverage.moz.tools/docs/
.. _staging: https://coverage.staging.moz.tools/docs/
.. _codecov.io: https://codecov.io/gh/marco-c/gecko-dev
.. _coveralls.io: https://coveralls.io/github/marco-c/gecko-dev
.. _ActiveData: https://wiki.mozilla.org/EngineeringProductivity/Projects/ActiveData
