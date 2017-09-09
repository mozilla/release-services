import requests
from flask import abort
from urllib.parse import urljoin


class HttpRequestHelper():
    def __init__(self, base_url):
        self.base_url = base_url

    def _get_url(self, endpoint):
        return urljoin(self.base_url, endpoint)

    def get(self, endpoint, **query_string):
        url = self._get_url(endpoint)
        qs_parameters = query_string if query_string else None
        resp = requests.get(url, params=qs_parameters)
        if resp.status_code == requests.codes.ok:
            return resp.json()
        abort(resp.status_code)
