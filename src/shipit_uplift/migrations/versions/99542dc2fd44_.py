"""empty message

Revision ID: 99542dc2fd44
Revises: 3c2d234e2d75
Create Date: 2017-10-09 20:09:28.170070

"""

# revision identifiers, used by Alembic.
revision = '99542dc2fd44'
down_revision = '3c2d234e2d75'

from alembic import op


def upgrade():
    '''
    Remove aurora from releases
    '''
    op.execute('delete from shipit_uplift_analysis where name=\'aurora\'')


def downgrade():
    pass
