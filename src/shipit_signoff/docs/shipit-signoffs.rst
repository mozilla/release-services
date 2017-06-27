
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

A policy is a dictionary with two mandatory fields, `method` and `definition`.
The method defines how a policy should be resolved, and the two valid values are
`local` and `balrog`. A `local` policy is controlled by the shipit_signoff
component, and a `balrog` policy is one where balrog_ is authoritative.

A policy `definition` is a list of dictionaries. Each individual dictionary
is a possible policy that could be met. If all of the conditions of any
dictionary in the list is met, then the entire policy is considered complete.

The keys in a policy dictionary are either LDAP groups or email addresses. This
way, we are certain that if a key does not contain an `@` symbol, it refers to
an LDAP group, without the policy writer having to remember additional syntax.
The value for each dictionary element is the number of signoffs required to
meet that part of the policy. For email addresses, this must be `1`, as each
person may only sign off on a step once.

The following example shows a local policy - controlled by the shipit_signoff
component, with a single possible way to complete the policy. Two people who
are in the LDAP group `releng` must sign the step, and two people who are in
the LDAP group `relman` must also sign. Since each person is only permitted
to sign a step once, this means four unique individuals must sign the step
for it to be completed.

.. code-block:: json

    {
        'method': 'local',
        'definition': [
            {
                'releng': 2,
                'relman': 2
            }
        ]
    }

In this example, there are two ways to complete the policy. One option is the same
as the previous example, where two people from `releng` and two people from `relman`
could sign. The other option is for `person1@mozilla.com` to sign the policy.

In a more logical statement, this policy is `(two from releng AND two from relman) OR person1@mozilla.com`

.. code-block:: json

    {
        'method': 'local',
        'definition': [
            {
                'releng': 2,
                'relman': 2
            },
            {
                'person1@mozilla.com': 1,
            }
        ]
    }

In this final example, `person1@mozilla.com` must sign the step in any case. However,
the other signatures could either be 'Two people in the relman group' or 'Two people in the releng group'.
Note that 'Two people, who are either in releng or relman' will not be sufficient.

    .. code-block:: json

        {
            'method': 'local',
            'definition': [
                {
                    'relman': 2,
                    'person1@mozilla.com': 1
                },
                {
                    'releng': 2,
                    'person1@mozilla.com': 1,
                }
            ]
        }




.. _balrog: https://mozilla-balrog.readthedocs.io/en/latest/
