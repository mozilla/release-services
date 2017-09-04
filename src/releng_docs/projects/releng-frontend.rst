.. _releng-frontend-project:

Project: releng-frontend
========================

:production: https://mozilla-releng.net
:staging: https://staging.mozilla-releng.net
:contact: `Rok Garbas`_, (backup `Release Engineering`_)

A common frontend for all of the ``releng-*`` projects.

``releng-docs`` (which is a static html page) is deployed :ref:`using
Taskcluster deployment hook<deploy-taskcluster>` to S3 bucket (
`production <https://console.aws.amazon.com/s3/buckets/releng-production-docs>`_,
`staging <https://console.aws.amazon.com/s3/buckets/releng-staging-docs>`_).

.. _`Rok Garbas`: https://phonebook.mozilla.org/?search/Rok%20Garbas
.. _`Release Engineering`: https://wiki.mozilla.org/ReleaseEngineering#Contacting_Release_Engineering
