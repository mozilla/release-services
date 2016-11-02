import json
import hashlib


def compute_dict_hash(data):
    """
    Compute SHA1 hash of a Python dict
    """
    data_json = json.dumps(data, sort_keys=True, ensure_ascii=True)
    h = hashlib.sha1(data_json.encode('utf-8'))
    return h.hexdigest()

def gravatar(email):
    """
    Build a gravatar url from an email address
    """
    email = email.lower()
    h = hashlib.md5(email.encode('utf-8'))
    return 'https://www.gravatar.com/avatar/{}'.format(h.hexdigest())
