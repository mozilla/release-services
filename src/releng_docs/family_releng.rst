.. _services-releng:

Service family: ``src/releng_*``
================================

Releng service family is a collection of smaller services with a common
frontend (``src/releng_frontend``) interface.


.. _releng_archiver:

``src/releng_archiver``
-----------------------

TODO: write description


.. _releng_clobberer:

``src/releng_clobberer``
------------------------

TODO: write description


.. _releng_docs:

``src/releng_docs``
-------------------

TODO: write description


.. _releng_frontend:

``src/releng_frontend``
-----------------------

:staging: https://staging.mozilla-releng.net
:production: https://mozilla-releng.net

TODO: write description


.. _releng_mapper:

``src/releng_mapper``
---------------------

TODO: write description


.. _releng_notification_identity:

``src/releng_notification_identity``
------------------------------------

:staging: https://notification-identity.staging.mozilla-releng.net
:production: https://notification-identity.mozilla-releng.net

RelEng Notification Identity is a tool to store the notification preferences of different individuals and groups for
different levels of urgency. Parties who will be notified of events related to the release cycle (human decisions,
signoffs, chemspills etc) register their identity name, and specify how to notify based on different levels of urgency.
Currently *email* is the only supported notification channel, and *low, normal, high, do it yesterday* are the
urgency levels. RelEng Notification Identity is meant to work together with RelEng Notification Policy.

.. _releng_notification_policy:

``src/releng_notification_policy``
----------------------------------

:staging: https://notification-policy.staging.mozilla-releng.net
:production: https://notification-policy.mozilla-releng.net

RelEng Notification Policy is a tool to send RelEng related notifications based on periodic policies, and escalate
unacknowledged notifications to higher urgency levels. Message requests are sent to the service with details on who to
notify and how urgent the message is. Policies for how to notify these stakeholders are retrieved from the RelEng
Notification Identity service.


.. _releng_slavehealth:

``src/releng_slavehealth``
--------------------------

TODO: write description


.. _releng_tooltool:

``src/releng_tooltool``
-----------------------

TODO: write description


.. _releng_treestatus:

``src/releng_treestatus``
-------------------------


:staging: https://treestatus.staging.mozilla-releng.net
:production: https://treestatus.mozilla-releng.net


TreeStatus is a relatively simple tool to keep track of the status of the
"trees" at Mozilla.  A "tree" is a version-control repository, and can
generally be in one of three states: open, closed, or approval-required. These
states affect the ability of developers to push new commits to these
repositories. Trees typically close when something prevents builds and tests
from succeeding.

The tree status tool provides an interface for anyone to see the current status
of all trees. It also allows "sheriffs" to manipulate tree status.

In addition to tracking the current state, the tool provides a log of changes
to tree states It also provides a "stack" of remembered previous states, to
make it easy to re-open after a failure condition is resolved.

.. note::

    Changes to a tree's message of the day are not logged, nor stored in the
    stack.


Compatibility Endpoints
^^^^^^^^^^^^^^^^^^^^^^^

The paths ``/treestatus/v0/trees/`` and ``/treestatus/v0/trees/<tree>`` provide
the same data as ``/treestatus/trees`` and ``/treestatus/trees/<tree>``, but
without the ``result`` wrapper object.  These paths provide support for the API
calls used against https://treestatus.mozilla.org.
