import os

basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URIS = dict(
    clobberer='sqlite:///' + os.path.join(basedir, 'app.db'),
)
