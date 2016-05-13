import os

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    raise Exception("You need to specify DATABASE_URL variable.")

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URIS = dict(
    clobberer=DATABASE_URL
)
