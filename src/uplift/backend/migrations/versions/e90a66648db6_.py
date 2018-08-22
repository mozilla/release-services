"""empty message

Revision ID: e90a66648db6
Revises: 35fdb610712b
Create Date: 2017-03-27 16:37:23.283917

"""

# revision identifiers, used by Alembic.
revision = 'e90a66648db6'
down_revision = '35fdb610712b'

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


def upgrade():
    op.drop_constraint('uniq_patch_status_group', 'shipit_uplift_patch_status', type_='unique')
    op.create_unique_constraint('uniq_patch_status_group', 'shipit_uplift_patch_status', ['bug_id', 'group', 'branch', 'revision'])


def downgrade():
    op.drop_constraint('uniq_patch_status_group', 'shipit_uplift_patch_status', type_='unique')
    op.create_unique_constraint('uniq_patch_status_group', 'shipit_uplift_patch_status', ['bug_id', 'group', 'revision'])
