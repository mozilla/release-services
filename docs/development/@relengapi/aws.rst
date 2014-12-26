Using AWS
=========

RelengAPI provides a light wrapper around `Boto <http://boto.readthedocs.org/>`_ for access to AWS resources.
The wrapper is accessible at ``current_app.aws``, which is an instance of :py:class:`relengapi.lib.aws.AWS`:

.. py:class:: relengapi.lib.aws.AWS

    Generic methods:

    .. py:method:: connect_to(service_name, region_name)

        :param string service_name: name of the service to connect to (e.g., `sqs`)
        :param string region_name: name of the region in which to connect (e.g., `us-west-2`)
        :returns: Boto connection instance

        This low-level method wrapps the various ``boto.connect_foo`` methods, handling authentication, regions, and caching of connections.

    SQS-related methods:

    .. py:method:: get_sqs_queue(relengapi_name)

        :param string relengapi_name: internal name of the queue
        :returns: Boto Queue instance

        Fetches the configuration for the named queue, then gets the corresponding boto Queue instance.
        Subsequent operations on the queue should use the Boto interface directly.
        In most cases, you'll want :py:meth:`sqs_write` instead

    .. py:method:: sqs_write(relengapi_name, body)

        :param string relengapi_name: internal name of the queue
        :param body: JSON-able data to be placed in the message body

        Writes ``body`` to the given queue.
        This uses WSME to JSON-ify the body, after which Boto base64-encodes the JSON content as AWS recommends.
        If possible, blueprints should use the same WSME types as the HTTP responses for SQS messages.
