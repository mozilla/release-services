.. _notification-project:

Project: notification/policy
===================================

:production: https://policy.notification.mozilla-releng.net
:staging: https://policy.notification.staging.mozilla-releng.net
:contact: `Rok Garbas`_, (backup `Release Engineering`_)

RelEng Notification Policy is a tool to schedule notifications requiring an "escalation path". Message requests are
sent to the service with the message contents and a list of "policies". Each policy contains a start and end time, a
notification frequency, an urgency and an identity to notify (retrieved from the RelEng Notification Identity service).
Escalation paths can be formed by increasing the urgency level of messages over time, increasing message urgency or
sending messages to more individuals if the message is not acknowledged by a certain time. Notifications are triggered
via a hook/ticktock endpoint. When the endpoint is triggered, the service will retrieve all unacknowledged messages
and send notifications according to any policy with a valid start/end time.


Project: notification/identity
==============================

:production: https://notification-identity.mozilla-releng.net
:staging: https://notification-identity.staging.mozilla-releng.net
:contact: `Rok Garbas`_, (backup `Release Engineering`_)

RelEng Notification Identity is a tool to store the notification preferences of parties involved in the release process.
Parties who will be notified of events related to the release cycle (human decisions, signoffs, chemspills etc) register
a name/identifier, and specify how to notify based on different levels of urgency.  Currently *email* and *irc* are the
only supported notification channels, and *low, normal, high* are the urgency levels.


.. _`Rok Garbas`: https://phonebook.mozilla.org/?search/Rok%20Garbas
.. _`Release Engineering`: https://wiki.mozilla.org/ReleaseEngineering#Contacting_Release_Engineering
