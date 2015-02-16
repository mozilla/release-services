# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

from itsdangerous import BadData


class FakeSerializer(object):

    @staticmethod
    def prm(id):
        return FakeSerializer.dumps(
            {"iss": "ra2", "jti": "t%d" % id, "typ": "prm"})

    @staticmethod
    def tmp(nbf, exp, prm, mta):
        return FakeSerializer.dumps(
            {"iss": "ra2", "typ": "tmp", 'nbf': nbf,
             "exp": exp, "prm": prm, "mta": mta})

    @staticmethod
    def dumps(data):
        return 'FK:' + json.dumps(data,
                                  separators=(',', ':'),
                                  sort_keys=True)

    @staticmethod
    def loads(data):
        if data[:3] != 'FK:':
            raise BadData('Not a fake token')
        else:
            return json.loads(data[3:])
