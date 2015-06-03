.. _Auth-Token-Config:

Token Authentication
====================

RelengAPI has a flexible token-based authentication mechanism, described in :ref:`Token-Usage`.
The temporary token type poses a risk if users are permitted to generate tokens with an arbitrary lifetime.
In such a case, a user could generate a 100-year temporary token, then continue to use that token after their user account has been terminated.
The ``RELENGAPI_TMP_TOKEN_MAX_LIFETIME`` configuration argument gives the longest validity lifetime allowable for a temporary token, in seconds.
It is treated as an offset from the current time, so it is enforced regardless of the "not-before" time.
The default value is ``86400``, equivalent to one day.


