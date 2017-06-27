from flask import current_app as app

import balrogclient


# TODO: Move to balrogclient lib
class CurrentUser(balrogclient.api.API):
    url_template = '/users/current'
    prerequest_url_template = '/users/current'
    url_template_vars = {}
