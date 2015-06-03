# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re

# Todo this mapping REALLY needs a non-hardcoded home
_slave_type = {
    "bld-linux64-ec2": [
        re.compile("^bld-centos6-hp-"),
        re.compile("^bld-linux64-ec2-"),
        re.compile("^bld-linux64-ix-"),
        re.compile("^b-linux64-ix-"),
        re.compile("^bld-linux64-spot-"),
        re.compile("^b-linux64-hp-"),
        re.compile("^try-linux64-spot-"),
        ],
    "bld-lion-r5": [
        re.compile("^bld-lion-r5-"),
        ],
    "b-2008-ix": [
        re.compile("^b-2008-ix-"),
        re.compile("^b-2008-sm-"),
        re.compile("^w64-ix-"),
        ],
    "tst-linux64-ec2": [
        re.compile("^talos-linux64-ix-"),
        re.compile("^tst-linux64-spot-"),
        re.compile("^tst-linux64-ec2-"),
        ],
    "tst-linux32-ec2": [
        re.compile("^talos-linux32-ix-"),
        re.compile("^tst-linux32-spot-"),
        re.compile("^tst-linux32-ec2-"),
        ],
    "t-yosemite-r5": [
        re.compile("^t-yosemite-r5-"),
        ],
    "talos-mtnlion-r5": [
        re.compile("^talos-mtnlion-r5-"),
        ],
    "t-snow-r4": [
        re.compile("^t-snow-r4-"),
        re.compile("^talos-r4-snow-"),
        ],
    "t-w732-ix": [
        re.compile("^t-w732-ix-"),
        ],
    "t-w864-ix": [
        re.compile("^t-w864-ix-"),
        ],
    "t-xp32-ix": [
        re.compile("^t-xp32-ix-"),
        ],
    }

_gpo_needed = [
    "b-2008-ix", "t-w732-ix", "t-w864-ix", "t-xp32-ix"
    ]


def slave_patterns():
    vals = []
    ret = {}
    for key, values in _slave_type.items():
        for regex in values:
            vals += [regex.pattern[1:] + "*"]
        vals.sort()
        ret[key] = vals
        vals = []
    return ret


def slave_to_slavetype(slave):
    if slave in _slave_type.keys():
        return slave
    for key, values in _slave_type.items():
        for regex in values:
            if regex.match(slave):
                return key
    return None


def is_aws_serviceable(slave):
    slaveclass = slave_to_slavetype(slave)
    if 'ec2' in slaveclass:
        return True
    return False


def needs_gpo(slave):
    slaveclass = slave_to_slavetype(slave)
    if slaveclass in _gpo_needed:
        return True
    return False


def slave_filter(slave_class):
    def _inner_slave_filter(item):
        for i in _slave_type[slave_class]:
            if i.match(item["name"]):
                return True
        return False  # If we got here, no match
    return _inner_slave_filter


def slavetype_to_awsprefix(slave_class):
    if not is_aws_serviceable(slave_class):
        raise ValueError("Unsupported Slave")
    basic_slave_prefix = slave_to_slavetype(slave_class)
    if basic_slave_prefix.startswith("bld"):
        loan_prefix = basic_slave_prefix.replace("bld-", "dev-")
    elif basic_slave_prefix.startswith("tst"):
        loan_prefix = basic_slave_prefix
    else:
        raise ValueError("Unsure how to name this aws slave")
    return loan_prefix
