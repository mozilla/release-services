from flask import current_app as app

import requests


def get_current_user_roles():
    user_info = requests.get(
        "{}/users/current".format(app.config['BALROG_API_ROOT']),
        auth=(app.config['BALROG_USERNAME'], app.config['BALROG_PASSWORD']),
    )
    return user_info.get("roles", {}).keys()


def make_signoffs_uri(policy_definition):
    return "{}/scheduled_changes/{}/{}/signoffs".format(
        app.config['BALROG_API_ROOT'],
        policy_definition['object'],
        policy_definition['sc_id'],
    )


def get_signoff_status(policy_definition):
    return requests.get(make_signoffs_uri(policy_definition))
