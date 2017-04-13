Contributing
============

Make sure you read the :ref:`prerequirements` document.

To get code you need to clone `mozilla-releng/services`_ repository.

.. code-block:: bash

    % git clone https://github.com/mozilla-releng/services/
    % cd services/


.. _branching-policy:

Branching policy
----------------

In above command we also listed all remote branches. To describe what each
branch is for:

- ``master``: The main development branch.

- ``staging``: The staging (eg. before production) branch, where all services
  are automatically deployed and are accessible under
  <service>.staging.mozilla-releng.net

- ``production``: The production branch, where all services are also
  automatically deployed and are accessible under <service>.mozilla-releng.net.

For more details of deployments, please look at specific service documentation
(eg: documentation for :ref:`Clobberer service <releng_clobberer>`).


Pull Requests
-------------

When submitting a **pull request** a build job for each service is being ran to
ensure that all tests across services are passing before you consider merging
it.


Commit style
------------

Prepend with service/library you are working on, eg. ``relegn_docs: more
details about clobberer service ...``


.. _`mozilla-releng/services`: https://github.com/mozilla-releng/services
