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
