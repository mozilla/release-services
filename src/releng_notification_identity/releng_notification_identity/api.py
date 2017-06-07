# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import
from flask import current_app
from typing import List, Tuple
from werkzeug.exceptions import BadRequest, Conflict, NotFound
from .models import Identity, Preference
from sqlalchemy.exc import IntegrityError


def _get_identity_preferences(identity_name: str) -> List[Preference]:
    session = current_app.db.session

    identity = session.query(Identity).filter(Identity.name == identity_name).first()
    if identity:
        preferences = session.query(Preference).filter(identity.id == Preference.identity).all()
        return preferences

    else:
        raise NotFound('Identity with name {} could not be found.'.format(identity_name))


def put_identity(identity_name: str, body: dict) -> Tuple[None, int]:
    try:
        session = current_app.db.session

        if session.query(Identity).filter(Identity.name == identity_name).count():
            raise Conflict('Identity with the name {} already exists'.format(identity_name))

        new_identity = Identity(name=identity_name)
        session.add(new_identity)
        session.flush()

        preferences = [
            Preference(**pref, identity=new_identity.id)
            for pref in body['preferences']
        ]

        session.add_all(preferences)
        session.commit()

        return None, 200

    except IntegrityError as ie:
        raise BadRequest('Request preferences contain duplicate urgency level {}.'.format(ie.params.get('urgency')))


def post_identity(identity_name: str, body: dict) -> Tuple[None, int]:
    session = current_app.db.session
    preference_records = _get_identity_preferences(identity_name)
    new_preference_lookup = {
        new_preference['urgency']: new_preference
        for new_preference in body['preferences']
    }

    for record in preference_records:
        if record.urgency not in new_preference_lookup:
            continue

        new_preference = new_preference_lookup[record.urgency]

        record.channel = new_preference['channel']
        record.target = new_preference['target']

        session.merge(record)
    session.commit()

    return None, 200


def get_identity(identity_name: str) -> Tuple[dict, int]:
    preferences = _get_identity_preferences(identity_name)
    if preferences:
        return {
            'preferences': [
                {**pref.to_dict(), 'name': identity_name}
                for pref in preferences
            ],
        }, 200

    else:
        raise NotFound('No preferences found for identity {}.'.format(identity_name))


def get_identity_preference_by_urgency(identity_name: str, urgency: str) -> Tuple[dict, int]:
    preferences = _get_identity_preferences(identity_name)
    preference_by_urgency_level = list(filter(lambda pref: pref.urgency == urgency, preferences))[0]
    if preference_by_urgency_level:
        return {
            'preferences': [
                {
                    'name': identity_name,
                    **preference_by_urgency_level.to_dict(),
                }
            ],
        }, 200

    else:
        raise NotFound('No preferences found for identity {}.'.format(identity_name))
