Logging
=======

Development
-----------

During development, logging output simply appears on the console.

Mod_wsgi
--------

In a deployment with ``mod_wsgi``, different types of errors appear in different logfiles.
It's best to check all three if you're seeing strange behavior.
These logfiles are

 * the general (not vhost-specific) apache logfile, e.g., ``/var/log/httpd/error_log``,
 * the virtualhost logfile, e.g., ``/var/log/httpd/$hostname/error_log``, or
 * the Python ``logging`` module's output - at ``/var/log/relengapi/relengapi.log`` at Mozilla.

Errors that prevent the ``.wsgi`` file from loading are logged to Apache's virtualhost log file.
This is most often a result of import errors or issues with a virtualenv.
Exceptions captured by the WSGI middleware are also logged to the virtualenv log file.

Errors and logging via the Python logging module does *not* appear in the Apache error logs.

It's easy to configure the logging module to log to syslog or some other destination within the ``.wsgi`` file::

    root = logging.getLogger('')
    root.setLevel(logging.NOTSET)
    syslog_formatter = logging.Formatter(
        '%(asctime)s ' + socket.gethostname() + ' relengapi: %(message)s', datefmt='%b %d %H:%M:%S')
    sys_log = logging.handlers.SysLogHandler(socktype=socket.SOCK_DGRAM)
    sys_log.setLevel(logging.INFO)
    sys_log.setFormatter(syslog_formatter)
    root.addHandler(sys_log)


Celery
------

It's a little tricky to make Celery cooperate -- its logging configuration is aggressive and inflexible.

One option is to replace the ``celery`` binary with a script of your own making that goes something like this::

    def setup(sender=None, logger=None, loglevel=None, logfile=None, format=None, colorize=None, **kwargs):
        # celery deletes this module during its initialization, so we have to do imports late
        import logging
        import socket
        syslog_formatter = logging.Formatter(
            '%(asctime)s ' + socket.gethostname() + ' relengapi: %(message)s', datefmt='%b %d %H:%M:%S')
        sys_log = logging.handlers.SysLogHandler(socktype=socket.SOCK_DGRAM)
        sys_log.setLevel(logging.INFO)
        sys_log.setFormatter(syslog_formatter)
        logger.addHandler(sys_log)

    from celery.signals import after_setup_logger, after_setup_task_logger
    # celery deletes this module during its initialization, so don't let it use a weak reference
    after_setup_logger.connect(setup, weak=False, dispatch_uid='asl')
    after_setup_task_logger.connect(setup, weak=False, dispatch_uid='astl')

    # finally, run celery
    import sys
    from pkg_resources import load_entry_point
    ep = load_entry_point('celery', 'console_scripts', 'celery')

Structured Logging
------------------

Releng API uses `structlog <https://structlog.readthedocs.org/>`_ internally to handle structrured log output.
To format log output as JSON, set the ``JSON_STRUCTURED_LOGGING`` setting to ``True``.

Note, however, that logging output produced by non-RelengAPI code (e.g., Celery, SQLAlchemy) will not be JSON-formatted.
Consumers must be able to accept non-JSON inputs.

Request IDs
-----------

By default, RelengAPI will invent a "request ID" for each request it receives, and include that in all logging during the request handling.
If you are deploying RelengAPI behind a load balancer or other service which has its own request IDs (such as Heroku's `HTTP Request IDs <https://devcenter.heroku.com/articles/http-request-id>`_), you can use those instead.
Set ``REQUEST_ID_HEADER`` to the name of the header containing the request id; for example::

    REQUEST_ID_HEADER = "X-Request-Id"
