Configure DNS
=============

All services are currently served under ``mozilla-releng.net`` domain.
A production instance of ``example`` project would be available under
``example.mozilla-releng.net`` and its staging instance would be available
under ``example.staging.mozilla-releng.net``.

Domains for projects  with Route53 Amazon service via Terraform configuration
you can find at:

https://github.com/mozilla-releng/build-cloud-tools/blob/master/terraform/base/route53.tf

Create needed changes and submit a Pull Request and contact `@dividehex`_ for a
review.

.. _`@dividehex`: https://github.com/dividehex
