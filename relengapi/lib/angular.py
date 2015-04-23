# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

from flask import current_app
from flask import render_template
from flask import request
from flask import url_for
from flask.ext.login import current_user
from relengapi import p
from relengapi.lib import permissions


def template(template_name, *dependency_urls, **initial_data):
    # find and load the template, based on the current request
    if request.blueprint:
        parent = current_app.blueprints[request.blueprint]
    else:
        parent = current_app
    if not parent.has_static_folder:
        raise RuntimeError("No static folder for angular template")
    template_path = os.path.join(parent.static_folder, template_name)
    template = open(template_path).read().decode('utf-8')

    # calculate the stylesheet and script links, based on suffix
    stylesheets = [u for u in dependency_urls if u.endswith('.css')]
    scripts = [u for u in dependency_urls if u.endswith('.js')]
    scripts.append(url_for('static', filename='js/relengapi.js'))
    if set(dependency_urls) - set(stylesheets) - set(scripts):
        raise RuntimeError("dependency_urls must all be .css and .js files")

    # include info on the current user
    user = {}
    user['permissions'] = [permissions.JsonPermission(name='.'.join(prm), doc=prm.__doc__)
                           for prm in current_user.permissions]
    user['type'] = current_user.type
    if current_user.type == 'human':
        user['authenticated_email'] = current_user.authenticated_email
    initial_data['user'] = user

    # include the full list of available permissions
    initial_data['perms'] = {str(prm): doc for prm, doc in p}

    return render_template('angular.html',
                           template=template,
                           stylesheets=stylesheets,
                           scripts=scripts,
                           initial_data=initial_data)
