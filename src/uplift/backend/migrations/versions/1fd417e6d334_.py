"""empty message

Revision ID: 1fd417e6d334
Revises: 99542dc2fd44
Create Date: 2018-08-20 08:38:48.277187

"""

# revision identifiers, used by Alembic.
revision = '1fd417e6d334'
down_revision = '99542dc2fd44'

from alembic import op


tables = (
    # Tables
    'analysis',
    'analysis_bugs',
    'bug',
    'contributor',
    'contributor_bugs',
    'patch_status',

    # Sequences
    'analysis_id_seq',
    'bug_id_seq',
    'contributor_bugs_id_seq',
    'contributor_id_seq',
    'patch_status_id_seq',
)

def upgrade():
    for table in tables:
        from_table = 'shipit_uplift_{}'.format(table)
        to_table = 'uplift_backend_{}'.format(table)
        op.rename_table(from_table, to_table)


def downgrade():
    for table in tables:
        from_table = 'uplift_backend_{}'.format(table)
        to_table = 'shipit_uplift_{}'.format(table)
        op.rename_table(from_table, to_table)
