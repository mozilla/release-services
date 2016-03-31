Logging
=======

The Releng API uses `structlog <https://structlog.readthedocs.org/>`_ for logging.
In practice this works almost exactly like the standard library's logging.
At the top of each module, import ``structlog``, then create a global ``logger`` object::

    logger = structlog.get_logger()

This is sufficient for most cases.
For more advanced uses, follow the ``structlog`` documentation.
