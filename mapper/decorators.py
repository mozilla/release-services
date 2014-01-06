# mostly copied from blobber
import os
from IPy import IP
from bottle import parse_auth, request, HTTPError
from functools import wraps

from .config import security_config


def login_required(fn):
    """
    Decorator to ensure client uses Basic Auth, secure HTTPs and has the
    expected credentials. Should it fail in any of these, HttpError 401/403
    error codes are returned

    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if not auth:
            raise HTTPError(status=401,
                            x_blobber_msg='Authentication required!')
        req_user, req_passwd = parse_auth(auth)

        USER = os.environ.get("CLIENT_USERNAME")
        PASSWORD = os.environ.get("CLIENT_PASSWORD")
        if not USER or not PASSWORD:
            raise HTTPError(status=500,
                            x_blobber_msg='Client credentials unset on server!')

        if (req_user, req_passwd) != (USER, PASSWORD):
            raise HTTPError(status=403,
                            x_blobber_msg='Authentication failed!')
        return fn(**kwargs)

    return wrapper


def check_client_ip(fn):
    """
    Decorator to ensure client IP is in the allowed range specified in
    the config file. Should it fail, HttpError 403 is returned.

    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        client_ip = request.remote_addr
        if not client_ip or not ip_allowed(client_ip):
            raise HTTPError(status=403,
                            x_blobber_msg='Client IP not allowed to call server!')
        return fn(**kwargs)

    return wrapper


def attach_required(fn):
    """
    Decorator to ensure client sends a POST call that contains a file.
    Should it fail, HttpError 403 is returned.

    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        data = request.files.blob
        if not data.file:
            raise HTTPError(status=403,
                            x_blobber_msg='Missing uploaded file!')
        return fn(**kwargs)

    return wrapper


def ip_allowed(remote_addr):
    """
    Helper function for check_client_ip decorator. Runs client IP
    against all allowed subnets specified in config file. Should it
    fail to match any of them, False statement is returned.

    """
    allowed_ips = [IP(i) for i in security_config.get('allowed_ips', None)]
    ip = IP(remote_addr)
    # TODO remove; staging
#    return True
    return ip in allowed_ips
#    for i in allowed_ips:
#        if ip in i:
#            return True
    return False
