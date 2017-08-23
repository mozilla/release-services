Configure DNS
=============

All services are currently served under ``mozilla-releng.net`` domain.
A production instance of ``example`` project would be available under
``example.mozilla-releng.net`` and its staging instance would be available
under ``example.staging.mozilla-releng.net``.

Domains for projects  with Route53 Amazon service via Terraform configuration.
Route53 resources are generated with the following command:

.. code-block:: console

    $ ./please tools terraform-route53-config > route53.tf

Once Route53 resources are generated copy ``route53.tf`` file to
`buid-cloud-tools <https://github.com/mozilla-releng/build-cloud-tools/blob/master/terraform/base/route53.tf>`_
and submit a Pull Request and contact <TODO>.
