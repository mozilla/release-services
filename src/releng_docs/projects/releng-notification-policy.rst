.. _releng-notification-policy-project:

Project: releng-notification-policy
===================================

:production: https://notification-policy.mozilla-releng.net
:staging: https://notification-policy.staging.mozilla-releng.net
:contact: `Rok Garbas`_, (backup `Release Engineering`_)

RelEng Notification Policy is a tool to schedule notifications requiring an "escalation path". Message requests are
sent to the service with the message contents and a list of "policies". Each policy contains a start and end time, a
notification frequency, an urgency and an identity to notify (retrieved from the RelEng Notification Identity service).
Escalation paths can be formed by increasing the urgency level of messages over time, increasing message urgency or
sending messages to more individuals if the message is not acknowledged by a certain time. Notifications are triggered
via a hook/ticktock endpoint. When the endpoint is triggered, the service will retrieve all unacknowledged messages
and send notifications according to any policy with a valid start/end time.


.. _`Rok Garbas`: https://phonebook.mozilla.org/?search/Rok%20Garbas
.. _`Release Engineering`: https://wiki.mozilla.org/ReleaseEngineering#Contacting_Release_Engineering
