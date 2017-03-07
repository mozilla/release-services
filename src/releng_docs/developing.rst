Developing
==========

Database
--------

The development environment supports both **Sqlite** and **PostgreSQL** for the backends.

To setup the database engine used in development, you need to configure the runner used for your application in the :code:`Makefile`

Here are two examples:

 * :code:`shipit_uplift` uses the Postgres engine
 * :code:`shipit_workflow` uses the Sqlite engine

.. code-block:: bash

    develop-run-shipit_uplift: require-postgres develop-run-BACKEND
    develop-run-shipit_workflow: require-sqlite develop-run-BACKEND 

When running the backend through the Makefile, the environment variable :code:`DATABASE_URL` is set to the choosen engine.

Use this command line to run your application:

.. code-block:: bash

    make develop-run APP=<APP_NAME>

Sqlite
~~~~~~

For sqlite, you do not need to run anything else.

Postgresql
~~~~~~~~~~

To run the postgresql server (on port 9000), use this Makefile command:

.. code-block:: bash

    make develop-run-postgres APP=<APP_NAME>


Then you can run normally the backend application, it will automatically switch to the new Postgresl database (named with your app name)
