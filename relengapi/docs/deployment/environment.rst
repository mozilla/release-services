Deployment Environment
======================

RelengAPI is designed for flexible deployment.
It is a simple WSGI application that can run on a developer's laptop or in a production environment.

In practice, it runs on a cluster of VMs at Mozilla, using Apache Httpd and ``mod_wsgi``.
However, in principle nothing in the design of the system precludes hosting on services like `Elastic Beanstalk <http://aws.amazon.com/elasticbeanstalk/>`_, `Heroku <https://www.heroku.com/>`_ or `Mozilla's PaaS <https://wiki.mozilla.org/Paas_Apps>`_.

Mod_wsgi Configuration
----------------------

The Mozilla deployment of RelengAPI has a WSGI file that looks like this::

    import os
    this_dir = os.path.dirname(__file__) or os.getcwd()

    # activate the virtualenv containing relengapi's dependencies
    activate_this = os.path.join(this_dir, 'virtualenv', 'bin', 'activate_this.py')
    execfile(activate_this, dict(__file__=activate_this))

    # set up application logging
    import sys
    import logging
    import logging.handlers

    root = logging.getLogger('')
    root.setLevel(logging.NOTSET)

    formatter = logging.Formatter('%(asctime)s [%(name)s] %(message)s')

    apache_log = logging.StreamHandler(sys.stderr)
    apache_log.setLevel(logging.INFO)
    apache_log.setFormatter(formatter)

    from cloghandler import ConcurrentRotatingFileHandler
    relengapi_log = ConcurrentRotatingFileHandler('/var/log/relengapi/relengapi.log', 'a', 256*1024, 300)
    relengapi_log.setLevel(logging.INFO)
    relengapi_log.setFormatter(formatter)

    root.addHandler(apache_log)
    root.addHandler(relengapi_log)

    # load the wsgi app with its settings
    from relengapi.app import create_app
    import os
    os.environ['RELENGAPI_SETTINGS'] = os.path.join(this_dir, 'settings.py')
    application = create_app()

RelengAPI processes the ``Authorization`` header on its own to handle token authentication.
However, mod_wsgi filters this header out by default.
To fix this, set ``WSGIPassAuthorization On`` in your Apache configuration.
