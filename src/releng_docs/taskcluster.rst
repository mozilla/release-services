Taskcluster
===========


(Auto-)Deploying
----------------

Merging to either ``staging`` or ``production`` branches will trigger a test
run which if successfull will trigger a deployment.

To manually deploy from you computer you can run:


.. code-block:: bash

    % make deploy-staging APP=releng_clobberer ...
    % make deploy-production APP=releng_clobberer ...

Above commands are missing many secrets which you need to provide as variables
to make commands above. You can check how this is done on taskcluster via
``.taskcluster.sh`` script.

Secrets are retrived from `taskcluster secrets services`_ for each branch
separatly.

- master -> repo:github.com/mozilla-releng/services:branch:master
- staging -> repo:github.com/mozilla-releng/services:branch:staging
- production -> repo:github.com/mozilla-releng/services:branch:production


Cron (hook) tasks
-----------------

Apart from building projects and testing them ``mozilla-releng/services`` you
can also configure hooks for taskcluster alongside configuring your project
setup in github repo. Hooks are configured per branch. Example:

.. code-block:: nix

    mkBackend rec {
      name = "releng_clobberer";
      ...
      passthru = {
        ..
        taskclusterHooks = {
          master = {
            taskcluster_cache = mkTaskclusterHook {
              name = "create taskcluster cache";
              owner = "rgarbas@mozilla.com";
              schedule = [ "\*\/15 \* \* \* \* \*" ];
              taskImage = self.docker;
              taskCommand = [
                "flask"
                "taskcluster_workertypes" ">" "/taskcluster_cache.json"
              ];
            };
          };
        };
        ...
      };


.. _`taskcluster secrets services`: https://tools.taskcluster.net/secrets/


.. Current software stack
.. ----------------------

.. - Flask + OpenAPI (Swagger) based mini framework to easily create *typed* JSON
..   APIs
.. - Elm for frontend work
.. - Sphinx for documentation


.. Amazon
.. ------

..     TODO
..     s3 bucket naming scheme
..     how are users + policies setup
..     cloudfront+certificates
..     we should really automate this


.. Heroku
.. ------

.. we dont use Procfiles but we are pushing Docker images (new feature in heroku)
.. who to ask when you lack perm (eg. you can create but you can not remove app)
.. database (on heroku) ... one for many services.


.. Future
.. ------

.. vulnix
.. micro docker images
