import datetime
import pytz


def utcnow():
    return datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)


def utcfromtimestamp(timestamp):
    return datetime.datetime.utcfromtimestamp(timestamp).replace(tzinfo=pytz.UTC)


def dt_as_timezone(obj, dest_tzinfo):
    if not isinstance(obj, datetime.datetime):
        raise ValueError("Must pass a datetime object")
    if obj.tzinfo is None:
        raise ValueError("Must pass a timezone aware datetime object")
    return dest_tzinfo.normalize(obj.astimezone(dest_tzinfo))
