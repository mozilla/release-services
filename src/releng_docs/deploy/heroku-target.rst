.. _deploy-heroku-target:

Target: Heroku
==============

One of possible deployment targets is Heroku_.

While a more known way to deploy to Heroku is to use Procfile_, but that comes
with a drawback that we can not reuse Nix as a build tool and we would have to
come up with a Heroku specific instructions.

Luckily for us Heroku also allows us to push Docker images and Nix on the other
hand can also wrap the output in a Docker image format. More below...


.. _Heroku: https://heroku.com
.. _Procfile: https://devcenter.heroku.com/articles/procfile


Manual deployment 
-----------------

While we have an automated and regular (weekly) way how to deploy efficiently
all of our projects to all targets, sometimes it is desired to have an option
to manually deploy to only a single target.

To do a manual deployment you need to:

- ensure that you have all :ref:`requirements <develop-requirements>` installed
- checkout the revision you want to deploy
- and run ``./please tools deploy:HEROKU ...``

You can check all possible options of this command by appending ``--help`` at
the end. An example command to deploy ``releng-treestatus`` project to
production environment would be:

.. code-block:: console

    $ ./please tools deploy:HEROKU releng-treestatus \
            --heroku-app="releng-production-treestatus" \
            --extra-attribute=".deploy.production" \
            --taskcluster-secrets="repo:github.com/mozilla-releng/services:branch:production" \
            --taskcluster-client-id="..." \
            --taskcluster-access-token="..."

You will need to have a Taskcluster client with the following scopes:

- ``assume:hook-id:project-releng/services-production-*``
- ``assume:repo:github.com/mozilla-releng/services:branch:production``
- ``hooks:modify-hook:project-releng/services-production-*``
- ``queue:create-task:aws-provisioner-v1/releng-task``
- ``secrets:get:repo:github.com/mozilla-releng/services:branch:production``

I suggest you create a custom (and temporary) client via `Takcluster's Client
Manager`_, that should generate above needed ``--taskcluster-client-id`` and
``--taskcluster-access-token``.


Testing docker image locally
----------------------------

Above mentioned command would internally build docker image. It is also
possible to build docker image and run it locally.

To build docker image for ``releng-treestatus`` project do:

.. code-block:: console

    $ ./please tools build releng-treestatus \
        --extra-attribute="docker"
    $ realpath tmp/result-build-releng-treestatus-1
    /nix/store/...-docker-image-mozilla-releng-treestatus.tar.gz

A symlink to Docker image is create at ``tmp/result-build-releng-treestatus-1``
location. 

Now all you need to do is load image and run it:

.. code-block:: console

    $ cat tmp/result-build-releng-treestatus-1 | docker load
    $ docker images
    ...
    mozilla-releng-treestatus   1.0.0   7a7c7882c4a3   47 years ago   262 MB
    ...
    $ docker run mozilla-releng-treestatus:1.0.0


.. _`Takcluster's Client Manager`: https://tools.taskcluster.net/auth/clients/
