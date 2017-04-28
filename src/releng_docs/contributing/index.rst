Contributing
============

.. todo::

    move quickstart from front page here. It should explain in few commands how
    to get started in most common cases  and have pointers to other sections
    when things get complicated

.. todo::

    Need to explain:common qustion for development:

     - good-first-bugs

     - who to ask for advice? how

     - why do we want to work together (link to defending.rst)

     - how do we deploy (link to deplying.rst)

     - should i put my code i services repository or

     - naming scheme of packages (eg. it is ok to be boring and very explicit
       with names)

     - branching policy, how to name long living branches, linear history,
       commit format, who to ask for a review.

     - common packages and their feature: (1) cli_common, (2) backend_common,
       (3) frontend_common



.. toctree::
    :maxdepth: 4
    :includehidden:

    developing
    prerequirements
    continuous-integration
    database_migrations
    authentication

.. _branching-policy:

Branching policy
----------------

.. todo:: Need to review this part

In above command we also listed all remote branches. To describe what each
branch is for:

- ``master``: The main development branch.

- ``staging``: The staging (eg. before production) branch, where all services
  are automatically deployed and are accessible under
  <service>.staging.mozilla-releng.net

- ``production``: The production branch, where all services are also
  automatically deployed and are accessible under <service>.mozilla-releng.net.

- when collaborating you can push and share branches from
  mozilla-releng/services directly, prepend brnach name with the owner of the
  branch.

For more details of deployments, please look at specific service documentation
(eg: documentation for :ref:`Clobberer service <releng_clobberer>`).

Pull Requests
-------------

.. todo:: Need to review this part

When submitting a **pull request** a build job for each service is being ran to
ensure that all tests across services are passing before you consider merging
it.


Commit style
------------

.. todo:: Need to review this part

Prepend with service/library you are working on, eg. ``relegn_docs: more
details about clobberer service ...``
