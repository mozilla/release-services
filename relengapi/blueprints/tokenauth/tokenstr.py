# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from flask import current_app
from itsdangerous import BadData
from itsdangerous import JSONWebSignatureSerializer

TOKENAUTH_ISSUER = 'ra2'
logger = logging.getLogger(__name__)


def init_app(app):
    if not app.secret_key:
        logger.warning("The `SECRET_KEY` setting is not set; tokens will be signed with "
                       "an insecure, static key")
    secret_key = app.secret_key or 'NOT THAT SECRET'
    app.tokenauth_serializer = JSONWebSignatureSerializer(secret_key)


def claims_to_str(claims):
    assert claims['iss'] == TOKENAUTH_ISSUER
    return current_app.tokenauth_serializer.dumps(claims)


def str_to_claims(token_str):
    try:
        claims = current_app.tokenauth_serializer.loads(token_str)
    except BadData:
        logger.warning("Got invalid signature in token %r", token_str)
        return None

    # convert v1 to ra2
    if claims.get('v') == 1:
        return {'iss': 'ra2', 'typ': 'prm', 'jti': 't%d' % claims['id']}

    if claims.get('iss') != TOKENAUTH_ISSUER:
        return None

    return claims


def jti2id(jti):
    if jti[0] != 't':
        raise TypeError('jti not in the format `t$token_id`')
    return int(jti[1:])
