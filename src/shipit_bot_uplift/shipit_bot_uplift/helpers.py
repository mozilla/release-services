from json import JSONEncoder, dumps as json_dumps
import re
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


def read_hosts():
    """
    Read /etc/hosts to get hostnames
    on a Nix env (used for taskclusterProxy)
    Only reads ipv4 entries to avoid duplicates
    """
    out = {}
    regex = re.compile('([\w:\-\.]+)')
    for line in open('/etc/hosts').readlines():
        if ':' in line:  # only ipv4
            continue
        x = regex.findall(line)
        if not x:
            continue
        ip, names = x[0], x[1:]
        out.update(dict(zip(names, [ip] * len(names))))

    return out
