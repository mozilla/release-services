Proxies
=======

In many cases, a request is best served by proxying to another HTTP server.
Fortunately, flask makes that easy, and Releng API makes it even easier::

    from relengapi.lib.proxy import proxy
    @bp.route('/other/resource'):
    def other_resource():
        return proxy('http://some-other-server.com/other/resource')

Note that, while this is reasonably effective, it is far less efficient than purpose-built proxies such as nginx, lighttpd, or mod_proxy.
