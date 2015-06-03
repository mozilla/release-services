.. _relengapi-sqs-listen:

AWS SQS
=======

RelengAPI consumes messages from SQS queues in a separate process from the web service.
To start this process, run

.. code-block:: none

    relengapi sqs-listen

In development, this command is generally run in a separate terminal.
In production, this command should be run on an appropriate set of instances -- either on each webhead, or in a dedicated auto-scaling group.
Bear in mind that web load may not scale at the same rate as queue-processing load.
