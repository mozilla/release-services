Safety Utilities
================

.. py:module:: relengapi.lib.safety

RelengAPI is a security-sensitive application, so it's important to avoid common mistakes.
While Werkzeug provides some utilities to help, this module supplements those with a few RelengAPI-specific tools.

Redirect URLs
-------------

RelengAPI must not expose any "open redirects", URLs which could result in an HTTP redirect with a URL of a attacker's choosing.
To avoid this, it is safest to not redirect to a URL provided by the user agent.
However, sometimes such redirects are convenient, especially after authentication.
In these cases, the next best approach is to refuse any redirects outside of the RelengAPI service itself.

.. py:function:: safe_redirect_path(url)

    :param url: the potentially dangerous URL
    :returns: a URL guaranteed to be within the RelengAPI service

    This method will return a relative path unchanged.
    For URLs with a network location or schema, it will return a path to the root of the RelengAPI service.
    Use it like this::

        return redirect(safe_redirect_path(url_from_user_agent))
