# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import releng_channel_status
from releng_channel_status.view import ChannelStatusView


app = releng_channel_status.create_app()
app.add_url_rule('/',
                 defaults={'rule_alias': app.config.get(
                     'DEFAULT_ALIAS'), 'product': None, 'channel': None},
                 view_func=ChannelStatusView.as_view('channel_status_default'))

app.add_url_rule('/<rule_alias>',
                 defaults={'product': None, 'channel': None},
                 view_func=ChannelStatusView.as_view('channel_status_alias'))

app.add_url_rule('/<product>/<channel>',
                 defaults={'rule_alias': None},
                 view_func=ChannelStatusView.as_view('channel_status_product_channel'))
