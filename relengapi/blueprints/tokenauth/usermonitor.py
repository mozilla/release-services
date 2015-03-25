# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import current_app
from relengapi.blueprints.tokenauth import tables
from relengapi.lib import badpenny


@badpenny.periodic_task(3600)
def monitor_users(job_status):
    # for every user token, examine the token's permission map and the user's
    # permissions.  If the token has more permissions than the user, disable
    # the token.
    session = current_app.db.session('relengapi')
    for token in session.query(tables.Token).filter(tables.Token.typ == 'usr'):
        token_perms = set(token.permissions)
        user_perms = current_app.authz.get_user_permissions(token.user)
        if user_perms is None:
            disable = True
        else:
            if token_perms - user_perms:
                disable = True
            else:
                disable = False

        if disable and not token.disabled:
            job_status.log_message("Disabling token %d for user %s" % (token.id, token.user))
            token.disabled = True
        elif not disable and token.disabled:
            job_status.log_message("Re-enabling token %d for user %s" % (token.id, token.user))
            token.disabled = False
    session.commit()


def init_app(app):
    pass
