Data Formats
============

.. _Datetime-Format:

Date / Time Values
------------------

Dates and times are represented in both responses and requests as ISO 8601 strings.
See `datetime.datetime.isoformat <https://docs.python.org/2/library/datetime.html#datetime.datetime.isoformat>`_ for details.
The resulting strings look like ``"2015-02-28T01:02:03+00:00"``.

Use of date/time values without timezone information is discouraged, and will be prohibited by `issue 177 <https://github.com/mozilla/build-relengapi/issues/177>`._
