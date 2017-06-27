
.. todo::

    explain purpose of signoff step


Architecture
************

.. graphviz::

    digraph "Signoffs Architecture" {
        "Signoffs Service" -> "Database";
        "Signoffs Service" -> "Balrog Admin API";
        "Signoffs Service" -> "Notifications Service";
        "Pipeline Service" -> "Signoffs Service";
        "Ship It UI" -> "Pipeline Service";
        "Ship It UI" -> "Signoffs Service";
        "User" -> "Ship It UI";
        "User" -> "Auth0";
        "User" -> "login.taskcluster.net";
        "Auth0" -> "Signoffs Service";
    }


Signoff Policies
****************

Over the wire and in memory, policies will be stored as lists of dictionaries.

For example, here is a native policy:

.. code-block:: json

    [
        {
            "users": ["userW", "userX"]
        },
        {
            "groups": {"groupY": 2, "groupZ": 2}
        }
    ]

In a native policy, each item in the list represents a way of reaching quorum
In the example above, quorum is reached when either userW and userX sign off
*or* when 2 people from groupY and 2 people from groupZ sign off.

Balrog-backed policies are much simpler:

.. code-block:: json

    {
        "sc_id": 23,
        "object": "rule"
    }

Balrog maintains its own set of signoff requirements and policies. The Signoffs
service simply needs to know which scheduled change to look at when trying to
find information about sign off requirements, et. al.
