Utilities
=========

.. py:module:: relengapi.util

.. py:function:: synchronized(lock)

    :param lock: a Lock instance

    This decorator will acquire and release the lock before and after the decorated funtion runs.
    The effect is that, for a given ``lock``, only one function decorated with ``@synchronized(lock)`` can execute at a time.

.. py:module:: relengapi.util.tz

.. py:function:: utcnow()

    Returns the datetime.datetime.utcnow() value, with added pytz.UTC tzinfo

.. py:function:: utcfromtimestamp(timestamp)

    :param timestamp: POSIX timestamp

    returns the datetime.datetime.utcfromtimestamp(timestamp) value with added pytz.UTC tzinfo

.. py:function:: dt_as_timezone(obj, dest_tzinfo)

    :param obj: a datetime object, with valid tzinfo
    :param dest_tzinfo: a timezone class as provided by pytz
    
    Converts the passed datetime into a new timezone. (According to world clock)
    
    example::

        import pytz
        from relengapi.util.tz import dt_as_timezone, utcnow
        dt = utcnow()
        print repr(dt)
        # datetime.datetime(2014, 5, 23, 16, 39, 32, 125099, tzinfo=<UTC>)
        print dt
        # 2014-05-23 16:39:32.125099+00:00
        repr(pytz.timezone("US/Pacific"))
        # <DstTzInfo 'US/Pacific' PST-1 day, 16:00:00 STD>
        repr(dt_as_timezone(dt, pytz.timezone("US/Pacific")))
        # datetime.datetime(2014, 5, 23, 9, 39, 32, 125099, tzinfo=<DstTzInfo 'US/Pacific' PDT-1 day, 17:00:00 DST>)
        print dt_as_timezone(dt, pytz.timezone("US/Pacific"))
        # 2014-05-23 09:39:32.125099-07:00
    
    .. note::
    
        Passing in a timezone unaware object will raise ValueError::
        
            import datetime
            dt2 = datetime.datetime.utcnow()
            dt_as_timezone(dt2, pytz.timezone("US/Pacific"))
            # Traceback (most recent call last):
            #   File "<stdin>", ....
            #   File ".../base/relengapi/util/tz.py", line 17, in dt_as_timezone
            #     raise ValueError("Must pass a timezone aware datetime object")
            # ValueError: Must pass a timezone aware datetime object
