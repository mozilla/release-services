import time
import re
import random
import base64
import hashlib
import json
import collections
import responses
from datetime import datetime, timedelta
from contextlib import contextmanager


def build_header(client_id, ext_data=None):
    """
    Build a fake Hawk header
    to share client id & scopes
    """

    out = collections.OrderedDict({
      'id': client_id,
      'ts': int(time.time()),
      'nonce': random.randint(0, 100000),
    })
    if ext_data is not None:
        json_data = json.dumps(ext_data, sort_keys=True).encode('utf-8')
        out['ext'] = base64.b64encode(json_data).decode('utf-8')

    mac_contents = '\n'.join(map(str, out.values()))
    out['mac'] = hashlib.sha1(mac_contents.encode('utf-8')).hexdigest()

    parts = map(lambda x: '{}="{}"'.format(*x), out.items())
    return 'Hawk {}'.format(', '.join(parts))


def parse_header(header):
    """
    Parse a fake Hawk header
    Extract client id and ext data
    """
    if not header.startswith('Hawk '):
        raise Exception('Missing Hawk prefix')

    # Load header parts
    parts = re.findall(r'(\w+)="([\w=\.\@\-_/]+)"', header)
    if parts is None:
        raise Exception('Invalid header structure')
    parts = dict(parts)
    for k in ('id', 'mac', 'ts', 'nonce'):
        if k not in parts:
            raise Exception('Missing header part {}'.format(k))

    # TODO: check mac

    # Load ext data
    try:
        ext_data = json.loads(base64.b64decode(parts['ext']).decode('utf-8'))
    except Exception:
        ext_data = {}

    return parts['id'], ext_data


def taskcluster_auth_mock(request):
    """
    Mock the hawk header validation from Taskcluster
    """
    payload = json.loads(request.body)
    try:
        # Parse fake hawk header
        if 'authorization' not in payload:
            raise Exception('Missing authorization')
        client_id, ext_data = parse_header(payload['authorization'])

        # Build success response
        expires = datetime.now() + timedelta(days=1)
        body = {
            'status': 'auth-success',
            'scopes': ext_data.get('scopes', []),
            'scheme': 'hawk',
            'clientId': client_id,
            'expires': expires.strftime('%Y-%m-%dT%H:%M:%S'),
        }
        http_code = 200

    except Exception as e:
        # Build failure response
        body = {
            'status': 'auth-failure',
            'message': str(e),
        }
        http_code = 401

    # Output response
    headers = {
        'Content-Type': 'application/json'
    }
    return (http_code, headers, json.dumps(body))


@contextmanager
def apply_mockups():
    """
    Apply the mockups responses
    """
    mock = responses.RequestsMock(assert_all_requests_are_fired=False)

    with mock:
        # Add a mock Taskcluster auth response
        mock.add_callback(
            responses.POST,
            'https://auth.taskcluster.net/v1/authenticate-hawk',
            callback=taskcluster_auth_mock,
            content_type='application/json',
        )

        yield mock


if __name__ == '__main__':
    h = build_header('test@test.com', {'ok': 42})
    print(h)
    print(parse_header(h))
