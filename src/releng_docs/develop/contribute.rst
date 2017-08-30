.. _develop-contribute:

Contribute
==========

If you like to get involved in the development of project mentioned in
``mozilla-releng/services``, there’re lots of areas where we could use some
help.

.. _develop-requirements:

Requirements
------------

These instructions assume you have the following installed (if not, you can
follow the links for installation instructions).

- `Git <https://git-scm.com/book/en/v2/Getting-Started-Installing-Git>`_
- `Docker <https://docs.docker.com/get-started>`_ or :ref:`Nix <develop-install-nix>`


Cloning the Repository
----------------------

- Fork the `mozilla-releng/services
  <https://github.com/mozilla-releng/services>`_ repository on GitHub.
- Clone the fork using

  .. code-block:: console

      $ git clone git@github.com:<your-github-username>/services.git

By creating a fork, you are able to generate a pull request so that the changes
can be easily seen and reviewed by other project members.


Usage
-----

Once these prerequisites are installed, run the following command to start the
desired project locally (eg. running locally in development mode):


.. code-block:: console

    $ ./please run <PROJECT>

To enter the development bash environment (eg. like virtualenv) use the
following command:

.. code-block:: console

    $ ./please shell <PROJECT>
    (nix-shell) $ which python
    /nix/store/.../bin/python


Running Tests
-------------

It is a good idea to run all tests to see if your project is running properly.

To execute all project's tests, run

.. code-block:: console

    $ ./please check <PROJECT>


Repository structure
--------------------

- **src/**: folder with all the projects
- **src/<PROJECT>**: folder with a <PROJECT> sources
- **lib/**: sources of libraries to help build projects in **src/**
- **nix/**: all nix related tools
- **./please**: a helper utility to drive development, testing and deployment.


Git workflow
------------

When you want to start contributing, you should create a branch from master.
This allows you to work on different projects at the same time.

.. code-block:: console

    $ git checkout master
    $ git checkout -b topic-branch

Once you’re done with your changes, you’ll need to describe those changes in
the commit message.


Submitting your work
--------------------

Once you have made the required changes, make sure all the tests still pass.
Then, you should submit your work with a pull request to master. Make sure you
reference the Bug number on the Pull Request. Now, you have to wait for the
review.

Once your code has been positively reviewed, it will be deployed shortly after.
So if you want feedback on your code, but it’s not ready to be deployed, you
should note it in the pull request.
