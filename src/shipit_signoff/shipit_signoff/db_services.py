from backend_common.db import db

from shipit_signoff.models import SignoffStep, Signature


def get_step_by_uid(step_uid):
    return db.session.query(SignoffStep).filter(SignoffStep.uid == step_uid).one()


def insert_new_signature(step, email, group_name):
    signature = Signature(step_uid=step.uid)
    signature.email = email
    signature.group = group_name

    db.session.add(signature)
    db.session.commit()
