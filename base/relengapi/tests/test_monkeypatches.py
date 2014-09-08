# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import Blueprint
from nose.tools import eq_


def test_Blueprint_root_widget():
    bp = Blueprint('test', __name__)
    eq_(bp.root_widget_templates or [], [])
    bp.root_widget_template('foo.html', priority=13)
    eq_(bp.root_widget_templates, [(13, 'foo.html', None)])


def test_Blueprint_root_widget_condition():
    bp = Blueprint('test', __name__)
    eq_(bp.root_widget_templates or [], [])

    def maybe():
        return False
    bp.root_widget_template('foo.html', priority=13, condition=maybe)
    eq_(bp.root_widget_templates, [(13, 'foo.html', maybe)])
