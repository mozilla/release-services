Sources / Branches
------------------

To get code you need to clone `services`_ repository.

.. code-block:: bash

    % git clone https://github.com/mozilla-releng/services/
    % cd services/
    % git branch --list -r
    origin/master
    origin/production
    origin/staging
    
In above command we also listed all remote branches. To describe what each
branch is for:

- ``master``: The main development branch.
- ``staging``: The staging (eg. before production) branch, where all services
  are automatically deployed and are accessible under
  <service>.staging.mozilla-releng.net
- ``production``: The production branch, where all services are also
  automatically deployed and are accessible under <service>.mozilla-releng.net.

For more details of deployments, please look at specific service documentation
(eg: documentation for :ref:`Clobberer service <service-clobberer>`).

When submitting a **pull request** a build job for each service is being ran to
ensure that all tests across services are passing before you consider merging
it.



