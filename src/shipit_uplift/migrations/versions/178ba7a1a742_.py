"""empty message

Revision ID: 178ba7a1a742
Revises: 46d559f516ea
Create Date: 2017-03-07 15:55:08.870342

"""

# revision identifiers, used by Alembic.
revision = '178ba7a1a742'
down_revision = '46d559f516ea'

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
        from_table = 'shipit_dashboard_{}'.format(table)
        to_table = 'shipit_uplift_{}'.format(table)
        op.rename_table(from_table, to_table)


def downgrade():
    for table in tables:
        from_table = 'shipit_uplift_{}'.format(table)
        to_table = 'shipit_dashboard_{}'.format(table)
        op.rename_table(from_table, to_table)
