Using AWS
=========

RelengAPI provides a light wrapper around `Boto <http://boto.readthedocs.org/>`_ for access to AWS resources.
The wrapper is accessible at ``current_app.aws``, which is an instance of :py:class:`relengapi.lib.aws.AWS`:

SQS
---

Amazon SQS provides simple queues with read and write operations.
From within a RelengAPI application, writing to a queue is trivial (:py:meth:`app.aws.sqs_write <relengapi.lib.aws.AWS.sqs_write>`).
However, reading from a queue requires a dedicated thread for that operation, and that thread does not run in the same process as the HTTP service.
Instead, all SQS readers run in a process started with ``relengapi sqs-listen``.
See :ref:`relengapi-sqs-listen` for more information.

Registering a listener in a blueprint can be a little tricky, since the decorator is connected to the application.
The application is available through ``@bp.record``::

    @bp.record
    def init_blueprint(state):
        app = state.app
        @app.aws.sqs_listen('us-west-2', 'my-queue')
        def my_queue_msg(msg):
            .. # process the message

Note that this pattern also makes it easy to get the region and queue name from the blueprint configuration.
Hard-coding this information is not a good idea!

AWS Class
---------

.. py:class:: relengapi.lib.aws.AWS

    Generic methods:

    .. py:method:: connect_to(service_name, region_name)

        :param string service_name: name of the service to connect to (e.g., `sqs`)
        :param string region_name: name of the region in which to connect (e.g., `us-west-2`)
        :returns: Boto connection instance

        This low-level method wrapps the various ``boto.connect_foo`` methods, handling authentication, regions, and caching of connections.

    SQS-related methods:

    .. py:method:: get_sqs_queue(region_name, queue_name)

        :param string region_name: name of the region in which to connect (e.g., `us-west-2`)
        :param string queue_name: name of the queue
        :returns: Boto Queue instance

        Fetches the configuration for the named queue, then gets the corresponding boto Queue instance.
        Subsequent operations on the queue should use the Boto interface directly.
        In most cases, you'll want :py:meth:`sqs_write` instead

    .. py:method:: sqs_write(region_name, queue_name, body)

        :param string region_name: name of the region in which to connect (e.g., `us-west-2`)
        :param string queue_name: name of the queue
        :param body: JSON-able data to be placed in the message body

        Writes ``body`` to the given queue.
        This uses WSME to JSON-ify the body, after which Boto base64-encodes the JSON content as AWS recommends.
        If possible, blueprints should use the same WSME types as the HTTP responses for SQS messages.

        To send messages with some other format (for example, without base64 encoding, or as simple strings), use :py:meth:`get_sqs_queue` to get a Queue instance, then construct and send the Message directly.


    .. py:method:: sqs_listen(region_name, queue_name, read_args)

        :param string region_name: name of the region in which to connect (e.g., `us-west-2`)
        :param string queue_name: name of the queue
        :param dictionary read_args: arguments to the boto ``Queue.read`` method

        Decorate the following function to receive messages from the named queue.

        The function will be called in the context of the RelengAPI application in the ``relengapi sqs-listen`` process.
        The ``read_args`` are passed as keyword arguments to `Queue.read <http://boto.readthedocs.org/en/latest/ref/sqs.html#boto.sqs.queue.Queue.read>`_, although ``wait_time_seconds`` is not available (it is already set).
