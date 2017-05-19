#. How are docker images organized?

- everything in one repo ``mozillareleng/services``

- services images are tagged as ``mozillareleng/services:<service>-<nixhash>``
  and are used for taskcluster taskcluster tasks

- base image ( ``mozillareleng/services:base-latest``) is the only one not
  built and :ref:`updated manually <building-base-docker-image>`


#. How are services docker images built?

.. todo:: Explain nix's dockerTools


.. building-base-docker-image

#. How to build base docker image (``mozillareleng/services:base-latest``)?

.. code-block:: console

    % git clone git@github.com:mozilla-releng/services.git
    % cd services
    % docker build -t base:latest base
    % docker tag base:latest mozillareleng/services:base-latest
    % docker login -u <username> -p "<password>"
    % docker push mozillareleng/services:base-latest

You can find credentials in the private repo at ``passwords/dockerhub.txt.gpg``

.. todo:: Explain ``nix/Dockerfile``



