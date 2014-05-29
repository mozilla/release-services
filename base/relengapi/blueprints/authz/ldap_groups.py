# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import ldap
import itertools
import logging
from flask.ext.principal import identity_loaded
from relengapi import p


class LdapGroups(object):

    def __init__(self, app):

        permissions_cfg = app.config.get('RELENGAPI_PERMISSIONS', {})
        self.group_permissions = permissions_cfg.get('group-permissions', {})

        # verify that each specified permission exists
        for perm in set(itertools.chain(*self.group_permissions.values())):
            try:
                p[perm]
            except KeyError:
                raise RuntimeError("invalid permission in settings: %r" % (perm,))

        self.uri = permissions_cfg['uri']
        self.login_dn = permissions_cfg['login_dn']
        self.login_password = permissions_cfg['login_password']
        self.user_base = permissions_cfg['user_base']
        self.group_base = permissions_cfg['group_base']
        self.debug = permissions_cfg.get('debug')

        self.logger = logging.getLogger(__name__)

        identity_loaded.connect_via(app)(self.on_identity_loaded)

    def get_user_groups(self, mail):
        if self.debug:
            self.logger.debug('Making LDAP query for %s', mail)
        try:
            l = ldap.initialize(self.uri)
            l.simple_bind_s(self.login_dn, self.login_password)
            # convert mail to DN
            people = l.search_s(self.user_base, ldap.SCOPE_SUBTREE,
                                '(&(objectClass=inetOrgPerson)(mail=%s))' % (mail,), [])
            if not people or len(people) != 1:
                return []
            user_dn = people[0][0]
            result = l.search_s(self.group_base, ldap.SCOPE_SUBTREE,
                                '(&(objectClass=groupOfNames)(member=%s))' % user_dn, ['cn'])
            groups = []
            for glist in [g[1]['cn'] for g in result]:
                groups.extend(glist)
            return list(set(groups))
        except ldap.LDAPError:
            self.logger.exception("While connecting to the LDAP server")
            return []

    def on_identity_loaded(self, sender, identity):
        # only attach identities for actual user logins; others are handled separately
        if identity.auth_type != 'user':
            return
        groups = self.get_user_groups(identity.id)
        if self.debug:
            self.logger.debug("Got groups %s for user %s", groups, identity.id)
        allowed_permissions = set()
        for group in groups:
            for perm in self.group_permissions.get(group, []):
                allowed_permissions.add(perm)
        if self.debug:
            self.logger.debug("Setting permissions %s for user %s",
                              ', '.join(allowed_permissions), identity.id)
        identity.provides.update([p[a] for a in allowed_permissions])
