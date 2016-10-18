Deploying
=========

Merging to either ``staging`` or ``production`` branches will, if build is
successfull, also trigger a deployment script. Deployment script will only
deploy services that were changed, since last deployment.

``mozilla-releng/services`` build system is flexible enough to deploy to many
different targets. Currently we deploy services to Heroku and Amazon S3, but
this can be extended to any other target.

Deploying of new services - at this time - does not handle creation/removal of
S3 buckets / Heroku applications. Those need to be created beforehand.

Manually deploying
------------------

To deploy a single service manually, you need to run:

.. code-block:: bash

    % make deploy-staging APP=releng_clobberer ...
        or
    % make deploy-production APP=releng_clobberer ...

Above commands are missing many secrets which you need to provide as variables
to make commands above. You can check how this is done on taskcluster via
``.taskcluster.sh`` script.

Secrets are retrived from `taskcluster secrets services`_ for each branch
separatly.

- staging => `repo:github.com/mozilla-releng/services:branch:staging`_
- production => `repo:github.com/mozilla-releng/services:branch:production`_


URL naming scheme
-----------------

URL naming scheme of deployed services is as following:

- ``src/releng_frontend``

  - staging => https://staging.mozilla-releng.net
  - production => https://mozilla-releng.net

- ``src/releng_SERVICE``

  - staging => https://SERVICE.mozilla-releng.net
  - production => https://SERVICE.staging.mozilla-releng.net

- ``src/shipit_frontend``

  - staging => https://shipit.staging.mozilla-releng.net
  - production => https://shipit.mozilla-releng.net

- ``src/shipit_SERVICE``

  - staging => https://SERVICE.shipit.mozilla-releng.net
  - production => https://SERVICE.shipit.staging.mozilla-releng.net


.. _deploying-docker:

Creating and pushing docker images
----------------------------------

``mozilla-releng/services`` build system also creates minimal docker images
which you can build and run locally. Building and pushing docker images to
``hub.docker.io`` does not require docker command and docker daemon line to be
installed.

To build and run a docker image for a service run:

.. code-block:: bash

    % make build-docker APP=releng_clobberer
    % cat ./result-docker-releng_clobberer | docker load

There is a convinient tool that can be used to pushed above generated docker
image tarball to ``hub.docker.io``. 

.. code-block:: bash

    % make build-tool-push
    % ./result-tool-push/bin/push \
		`realpath ./result-docker-releng_clobberer \
		https://index.docker.io \
		-u <HEROKU_USERNAME> \
		-p <HEROKU_PASSWORD> \
		-N <DOCKER_REPO> \
		-T <DOCKER_REPO_TAG>


Amazon
------

In order to make ``mozilla-releng/services`` work with Amazon following
configuration needed to be in place:

- 3 users are created (**RelEngDevelop**, **RelEngStaging**,
  **RelEngProduction**) and their api credentials stored in taskcluster
  secrets.

- 3 custom policies were created (TODO) to allow above created users to sync 

- 2 S3 buckets are created per each **src/*_frontend** application to hold
  frontend code.

- For each S3 bucket a CloudFront Policy is created and configured to

  - redirect every URL to ``index.html``
  - redirect from http to https

- A ``releng-cache`` S3 bucket is created and read/write/delete permission
  granted for all above created policies. This S3 bucket is used to hold binary
  files of builds.

- S3 buckets need to be created before deploying new service

TODO: write how certificates are handled once Route51 is configured


Heroku
------

We currently use a (quite some time in beta) Heroku feature that allows to run
docker images on Heroku infrastructure. To manually push docker images build in
:ref:`previous praragraph <deploying-docker>` you need to push docker images to
Heroku's custom docker registry.

.. code-block:: bash

    % make build-tool-push
	./result-tool-push/bin/push \
		`realpath ./result-docker-releng_clobberer` \
		https://registry.heroku.com \
		-u <HEROKU_USERNAME> \
		-p <HEROKU_PASSWORD> \
		-N <HEROKU_APP>/web \
		-T latest


.. _`taskcluster secrets services`: https://tools.taskcluster.net/secrets/
.. _`repo:github.com/mozilla-releng/services:branch:staging`: TODO
.. _`repo:github.com/mozilla-releng/services:branch:production`: TODO
