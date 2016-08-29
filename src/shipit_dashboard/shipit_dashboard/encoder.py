# coding=utf-8
from flask.json import JSONEncoder
from datetime import timedelta


class ShipitJSONEncoder(JSONEncoder):
    """
    Handles specific serializations:
     * timedelta
    """

    def default(self, obj):
        try:
            if isinstance(obj, timedelta):
                # Serialize timedelta as seconds
                return obj.total_seconds()
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)
