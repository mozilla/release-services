from flask import Flask, url_for, session, request, jsonify
from flask_oauthlib.client import OAuth
import requests


r = requests.get('http://euclid.r.igoro.us:8010/oauth/client')
j = r.json()
CLIENT_ID = j['client_id']
CLIENT_SECRET = j['client_secret']


app = Flask(__name__)
app.debug = True
app.secret_key = 'secret'
oauth = OAuth(app)

remote = oauth.remote_app(
    'remote',
    consumer_key=CLIENT_ID,
    consumer_secret=CLIENT_SECRET,
    request_token_params={'scope': 'email'},
    base_url='http://euclid.r.igoro.us:8010/oauth/',
    request_token_url=None,
    access_token_url='http://euclid.r.igoro.us:8010/oauth/token',
    authorize_url='http://euclid.r.igoro.us:8010/oauth/authorize'
)


@app.route('/')
def index():
    if 'remote_oauth' in session:
        resp = remote.get('secret')
        return jsonify(resp.data)
    next_url = request.args.get('next') or request.referrer or None
    return remote.authorize(
        callback=url_for('authorized', next=next_url, _external=True)
    )


@app.route('/authorized')
@remote.authorized_handler
def authorized(resp):
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    if isinstance(resp, Exception):
        return 'Access denied: ' + resp.message
    session['remote_oauth'] = (resp['access_token'], '')
    return jsonify(oauth_token=resp['access_token'])


@remote.tokengetter
def get_oauth_token():
    return session.get('remote_oauth')


if __name__ == '__main__':
    import os
    os.environ['DEBUG'] = 'true'
    app.run(host='0.0.0.0', port=8000)
