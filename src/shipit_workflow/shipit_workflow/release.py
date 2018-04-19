# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re

# If version has two parts with no trailing specifiers like "rc", we
# consider it a 'final' release for which we only create a _RELEASE tag.
FINAL_RELEASE_REGEX = '^\d+\.\d+$'


def is_final_release(version):
    return bool(re.match(FINAL_RELEASE_REGEX, version))


def is_beta(version):
    return 'b' in version


def is_esr(version):
    return 'esr' in version


def is_rc(version, partial_updates):
    if not is_beta(version) and not is_esr(version):
        if is_final_release(version):
            return True
        # RC release types will enable beta-channel testing &
        # shipping. We need this for all "final" releases
        # and also any releases that include a beta as a partial.
        # The assumption that "shipping to beta channel" always
        # implies other RC behaviour is bound to break at some
        # point, but this works for now.
        for version in partial_updates:
            if is_beta(version):
                return True
    return False


def bump_version(version):
    '''Bump last digit'''
    split_by = '.'
    digit_index = 2
    suffix = ''
    if 'b' in version:
        split_by = 'b'
        digit_index = 1
    if 'esr' in version:
        version = version.replace('esr', '')
        suffix = 'esr'
    v = version.split(split_by)
    if len(v) < digit_index + 1:
        # 45.0 is 45.0.0 actually
        v.append('0')
    v[-1] = str(int(v[-1]) + 1)
    return split_by.join(v) + suffix


def get_beta_num(version):
    if is_beta(version):
        parts = version.split('b')
        return int(parts[-1])


def is_partner_enabled(product, version, min_version=61):
    major_version = int(version.split('.')[0])
    if product == 'firefox' and major_version >= min_version:
        if is_beta(version):
            if get_beta_num(version) >= 8:
                return True
        elif not is_esr(version):
            return True
    return False
