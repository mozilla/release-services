from relengapi import db

class Version(db.Model):
    __bind_key__ = 'scheduler'

    version = db.Column(db.Integer, nullable=False)

# add more tables here as required
