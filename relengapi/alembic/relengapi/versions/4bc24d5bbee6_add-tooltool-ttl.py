"""Add column for tracking the time to live value
Revision ID: 4bc24d5bbee6
Revises: 993e4d841aa
Create Date: 2015-07-31 14:23:24.812148

"""
import relengapi
import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision = '4bc24d5bbee6'
down_revision = '993e4d841aa'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tooltool_files',
                  sa.Column('expires', relengapi.lib.db.UTCDateTime(), nullable=True))
    op.create_index(op.f('ix_tooltool_files_expires'), 'tooltool_files', ['expires'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_tooltool_files_expires'), table_name='tooltool_files')
    op.drop_column('tooltool_files', 'expires')
