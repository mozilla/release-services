
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
        "method": "local",
        "definition": [
            {
                "releng": 2,
                "relman": 2
            }
        ]
    }

In this example, there are two ways to complete the policy. One option is the same
as the previous example, where two people from `releng` and two people from `relman`
could sign. The other option is for `person1@mozilla.com` to sign the policy.

In a more logical statement, this policy is `(two from releng AND two from relman) OR person1@mozilla.com`

.. code-block:: json

    {
        "method": "local",
        "definition": [
            {
                "releng": 2,
                "relman": 2
            },
            {
                "person1@mozilla.com": 1,
            }
        ]
    }

In this final example, `person1@mozilla.com` must sign the step in any case. However,
the other signatures could either be 'Two people in the relman group' or 'Two people in the releng group'.
Note that 'Two people, who are either in releng or relman' will not be sufficient.

    .. code-block:: json

        {
            "method": "local",
            "definition": [
                {
                    "relman": 2,
                    "person1@mozilla.com": 1
                },
                {
                    "releng": 2,
                    "person1@mozilla.com": 1,
                }
            ]
        }

Balrog_-backed policies are much simpler:

.. code-block:: json

    {
        "sc_id": 23,
        "object": "rule"
    }

Balrog_ maintains its own set of signoff requirements and policies. The Signoffs
service simply needs to know which scheduled change to look at when trying to
find information about sign off requirements, et. al.


Balrog Interaction
******************

Although the Signoffs service delegates the tracking and enforcement of some Steps to Balrog,
it still must know when the Signoff requirements have been met in Balrog order to resolve a
Step as completed. Whenever a Step is created or status is requested for it, the Signoffs
service will talk to Balrog and update the Step's state to match Balrog. Note that *only* the
state is updated. To avoid potential inconsistencies between Balrog and the Signoff service,
we purposely avoid importing Balrog Signoffs as Signatures.

The Signoffs service also takes on the role of redirecting clients to Balrog when they attempt
to Signoff or revoke a Signoff on a Balrog based Step. This interaction looks as follows:

* The client makes a request to https://signoffs/step/1/sign.

* The Signoffs service talks to Balrog to check that the user holds the Balrog Role they need
  to make the Signoff. If the User does not hold that Role, a 403 is returned and nothing further
  happens.

* Otherwise, the Signoffs service returns a 307 with the appropriate Balrog URI in the Location
  header (eg: https://balrog/api/scheduled_changes/rules/72/signoffs).

* The client must rewrite the Balrog URI to get a CSRF token (eg: https://balrog/api/csrf_token),
  and change "group" to "role" in the request body.

* The client can then make a new request to the URI returned by the Signoffs service to perform
  the Signoff.

.. _balrog: https://mozilla-balrog.readthedocs.io/en/latest/
