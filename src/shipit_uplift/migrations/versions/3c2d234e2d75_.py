"""empty message

Revision ID: 3c2d234e2d75
Revises: e90a66648db6
Create Date: 2017-04-21 17:04:02.772137

"""

# revision identifiers, used by Alembic.
revision = '3c2d234e2d75'
down_revision = 'e90a66648db6'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.drop_column('shipit_uplift_analysis', 'parameters')


def downgrade():
    op.add_column('shipit_uplift_analysis', sa.Column('parameters', sa.TEXT(), autoincrement=False, nullable=True))
