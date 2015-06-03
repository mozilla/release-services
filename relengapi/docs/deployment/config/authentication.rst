.. _Deployment-Authentication:

Authentication
==============

Releng API supports a number of authentication mechanisms.
These are configured with the ``RELENGAPI_AUTHENTICATION`` key, which is a dictionary containing options.
The only required option is ``type``, which specifies the authentication type.

Browserid
~~~~~~~~~

If ``type`` is ``browserid``, no further options are required, as browserid is a very simple protocol.
Any user will be able to authenticate. ::

    RELENGAPI_AUTHENTICATION = {
        'type': 'browserid',
    }

External (proxy or environment)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's common to deploy webapps with authentication done by a frontend service.
In this case the app sees only the authenticated username, not the credentials used for authentication, thereby reducing the dissemination of those credentials.
The ``external`` authentication mechanism supports this.

In all cases, only the ``/userauth/login`` URL is checked for authentication.
The frontend must pass all other URLs through without requiring authentication, as they may be API calls authenticated with some other mechanism.

On success, the authentication information is cached in the Flask session.

If the ``header`` key is provided, then the API trusts a plaintext header from the HTTP client to specify the username.
This mode is intended for deployments where the only access to the server is from a frontend proxy which is performing authentication.
This is a common configuration with load balancers or with tools like Apache or Nginx configured using tools like ``mod_authnz_ldap``.
It is critical that such configuration not allow access directly to the Releng API process!  ::

    RELENGAPI_AUTHENTICATION = {
        'type': 'external',
        'header': 'X-Authenticated-User',
    }

If ``environ`` is given, then the API trusts an environment variable named by that key.
This is most useful when running in ``mod_wsgi``, where other server plugins can set environment variables.
For example, ``mod_authnz_ldap`` sets ``AUTHENTICATE_*`` environment variables that can be used for this purpose. ::

    RELENGAPI_AUTHENTICATION = {
        'type': 'external',
        'environ': 'AUTHENTICATE_MAIL',
    }

Constant
~~~~~~~~

In a development scenario, it can be helpful to always login as the same user, with no need for authentication. ::

    RELENGAPI_AUTHENTICATION = {
        'type': 'constant',
        'email': 'username@domain.com',
    }

Obviously this is not a safe alternative for a production deployment of RelengAPI.


