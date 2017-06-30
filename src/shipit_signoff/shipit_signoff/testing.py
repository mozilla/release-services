import json
import os.path

from flask import request, jsonify

def fake_auth():
    username = request.args.get('access_token')
    users = json.loads(open(os.path.join(os.path.dirname(__file__), 'fakeauth.json')).read())
    if username not in users:
        return b'Unauthorized'
    else:
        return jsonify(users.get(username))
