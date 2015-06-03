# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import itertools
import ldap
import logging

from relengapi import p
from relengapi.lib.auth import base
from relengapi.lib.auth import permissions_stale


class LdapGroupsAuthz(base.BaseAuthz):

    def __init__(self, app):

        permissions_cfg = app.config.get('RELENGAPI_PERMISSIONS', {})
        self.group_permissions = permissions_cfg.get('group-permissions', {})

        # verify that each specified permission exists
        for perm in set(itertools.chain(*self.group_permissions.values())):
            try:
                p[perm]
            except KeyError:
                raise RuntimeError(
                    "invalid permission in settings: %r" % (perm,))

        self.uri = permissions_cfg['uri']
        self.login_dn = permissions_cfg['login_dn']
        self.login_password = permissions_cfg['login_password']
        self.user_base = permissions_cfg['user_base']
        self.group_base = permissions_cfg['group_base']
        self.debug = permissions_cfg.get('debug')

        self.logger = logging.getLogger(__name__)

        permissions_stale.connect_via(app)(self.on_permissions_stale)

    def _groups_to_perms(self, groups):
        allowed_permissions = set(self.group_permissions.get('<everyone>', []))
        for group in groups:
            for perm in self.group_permissions.get(group, []):
                allowed_permissions.add(perm)
        return set([p[perm] for perm in allowed_permissions])

    def get_user_permissions(self, email):
        groups = self.get_user_groups(email)
        if groups is not None:
            return self._groups_to_perms(groups)
        else:
            return None

    def get_user_groups(self, mail):
        if self.debug:
            self.logger.debug('Making LDAP query for %s', mail)
        try:
            l = ldap.initialize(self.uri)
            l.simple_bind_s(self.login_dn, self.login_password)
            groups = []

            # convert mail to DN and search for groupOfNames with member=$dn
            people = l.search_s(self.user_base, ldap.SCOPE_SUBTREE,
                                '(&(objectClass=inetOrgPerson)(mail=%s))' % (mail,), [])
            if not people or len(people) != 1:
                return None
            user_dn = people[0][0]
            result = l.search_s(self.group_base, ldap.SCOPE_SUBTREE,
                                '(&(objectClass=groupOfNames)(member=%s))' % user_dn, ['cn'])
            for glist in [g[1]['cn'] for g in result]:
                groups.extend(glist)

            # Mozilla uses some POSIX groups, which have a different class.
            # The scm_level_N groups also have the unusual trait of using the mail
            # in the memberUid attribute; other POSIX groups use the actual uid,
            # and won't be matched by this clause
            result = l.search_s(self.group_base, ldap.SCOPE_SUBTREE,
                                '(&(objectClass=posixGroup)(memberUid=%s))' % mail, ['cn'])
            for glist in [g[1]['cn'] for g in result]:
                groups.extend(glist)

            return list(set(groups))
        except ldap.LDAPError:
            self.logger.exception("While connecting to the LDAP server")
            return None

    def on_permissions_stale(self, sender, user, permissions):
        groups = self.get_user_groups(user.authenticated_email)
        if self.debug:
            self.logger.debug("Got groups %s for user %s", groups, user)

        # when the user doesn't exist, no perms (not even <everyone>)
        if groups is None:
            return []
        allowed_permissions = self._groups_to_perms(groups)
        if self.debug:
            self.logger.debug("Setting permissions %s for user %s",
                              ', '.join(str(prm) for prm in allowed_permissions), user)
        permissions.update(allowed_permissions)


def init_app(app):
    app.authz = LdapGroupsAuthz(app)
