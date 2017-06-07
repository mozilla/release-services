# -*- coding: utf-8 -*-
from json import JSONEncoder, dumps as json_dumps
import hashlib
from datetime import timedelta, datetime


class ShipitJSONEncoder(JSONEncoder):
    """
    Handles specific serializations:
     * timedelta
     * datetime
    """
    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                # Serialize datetime
                return obj.isoformat()

            if isinstance(obj, timedelta):
                # Serialize timedelta as seconds
                return obj.total_seconds()

            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


def compute_dict_hash(data):
    """
    Compute SHA1 hash of a Python dict
    """
    data_json = json_dumps(data, sort_keys=True, ensure_ascii=True)
    h = hashlib.sha1(data_json.encode('utf-8'))
    return h.hexdigest()
