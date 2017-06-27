from flask import current_app as app

import requests


def get_current_user_roles():
    user_info = requests.get(
        "{}/users/current".format(app.config['BALROG_API_ROOT']),
        auth=(app.config['BALROG_USERNAME'], app.config['BALROG_PASSWORD']),
    )
    return user_info.get("roles", {}).keys()
