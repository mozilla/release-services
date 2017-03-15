Database Migrations
===================

Flask applications using ``backend_common.db`` app (enabled by default) support Database migrations through Flask-Migrate_ and Alembic_.

Migrations are stored in ``src/<APP_NAME>/migrations``. The specific migrations folder structure is automaticallty created by Flask-Migrate at runtime.


Add a migration
---------------

To create a database migration:

 * Create your changes in your application models.py file
 * Run the following command: 

.. code-block:: bash

    % make develop-flask-shell APP=<APP_NAME> FLASK_CMD="db migrate"

A new revision will be created in ``src/<APP_NAME>/migrations/versions``

As stated by the migrations tool, you should edit the generated file to check any potential issue.


Upgrade the database
--------------------

When you want to apply a migration to your database, simply run the following command:

.. code-block:: bash

    % make develop-flask-shell APP=<APP_NAME> FLASK_CMD="db upgrade"

Migrations on staging and production environments are automatically ran before the gunicorn process are ran.

Read the documentation to know more about `Flask operations`_

Fixtures
--------

One advantage of this system is that you can add some fixtures for a specific database structure version.

Edit any migration file for your application, and use the ``op.bulk_insert`` function to add items to your database. Read the documenattion to know more about bulk_insert_.

.. _Flask-Migrate: https://flask-migrate.readthedocs.io/en/latest/
.. _Flask operations: https://flask-migrate.readthedocs.io/en/latest/#command-reference
.. _Alembic: http://alembic.zzzcomputing.com/en/latest/
.. _bulk_insert: http://alembic.zzzcomputing.com/en/latest/ops.html?highlight=insert#alembic.operations.Operations.bulk_insert
