.. _releng-notification-identity-project:

Project: releng-notification-identity
=====================================

:production: https://notification-identity.mozilla-releng.net
:staging: https://notification-identity.staging.mozilla-releng.net
:contact: `Rok Garbas`_, (backup `Release Engineering`_)

RelEng Notification Identity is a tool to store the notification preferences of parties involved in the release process.
Parties who will be notified of events related to the release cycle (human decisions, signoffs, chemspills etc) register
a name/identifier, and specify how to notify based on different levels of urgency.  Currently *email* and *irc* are the
only supported notification channels, and *low, normal, high* are the urgency levels.

.. _`Rok Garbas`: https://phonebook.mozilla.org/?search/Rok%20Garbas
.. _`Release Engineering`: https://wiki.mozilla.org/ReleaseEngineering#Contacting_Release_Engineering
