TreeStatus
==========

TreeStatus is a relatively simple tool to keep track of the status of the "trees" at Mozilla.
A "tree" is a version-control repository, and can generally be in one of three states: open, closed, or approval-required.
These states affect the ability of developers to push new commits to these repositories.
Trees typically close when something prevents builds and tests from succeeding.

The tree status tool provides an interface for anyone to see the current status of all trees.
It also allows "sheriffs" to manipulate tree status.

In addition to tracking the current state, the tool provides a log of changes to tree states
It also provides a "stack" of remembered previous states, to make it easy to re-open after a failure condition is resolved.

.. note::


    Changes to a tree's message of the day are not logged, nor stored in the stack.

Types
-----

.. api:autotype::
    Tree
    TreeLog
    TreeStateChange
    TreeUpdate

Endpoints
---------

.. api:autoendpoint:: treestatus.*

Compatibility Endpoints
.......................

The paths ``/treestatus/compat/trees/`` and ``/treestatus/compat/trees/<tree>`` provide the same data as ``/treestatus/trees`` and ``/treestatus/trees/<tree>``, but without the ``result`` wrapper object.
These paths provide support for the API calls used against https://treestatus.mozilla.org.
