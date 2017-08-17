.. _releng-notification-identity-project:

Project: releng-notification-identity
=====================================

:production: https://notification-identity.mozilla-releng.net
:staging: https://notification-identity.staging.mozilla-releng.net
:contact: `Rok Garbas`_, (backup `Release Engineering`_)

RelEng Notification Identity is a tool to store the notification preferences of
different individuals and groups for different levels of urgency. Parties who
will be notified of events related to the release cycle (human decisions,
signoffs, chemspills etc) register their identity name, and specify how to
notify based on different levels of urgency.  Currently *email* is the only
supported notification channel, and *low, normal, high, do it yesterday* are
the urgency levels. RelEng Notification Identity is meant to work together with
RelEng Notification Policy.

.. _`Rok Garbas`: https://phonebook.mozilla.org/?search/Rok%20Garbas
.. _`Release Engineering`: https://wiki.mozilla.org/ReleaseEngineering#Contacting_Release_Engineering
