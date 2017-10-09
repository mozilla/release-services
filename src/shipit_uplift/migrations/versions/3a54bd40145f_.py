"""empty message

Revision ID: 3a54bd40145f
Revises: None
Create Date: 2016-11-02 15:21:54.736383

"""

# revision identifiers, used by Alembic.
revision = '3a54bd40145f'
down_revision = None

from alembic import op
import sqlalchemy as sa
import os
import json

from sqlalchemy.schema import CreateTable
from sqlalchemy.ext.compiler import compiles
import re


HERE = os.path.dirname(__file__)


@compiles(CreateTable)
def _add_if_not_exists(element, compiler, **kw):
    output = compiler.visit_create_table(element, **kw)
    output = re.sub("^\s*CREATE TABLE", "CREATE TABLE IF NOT EXISTS", output, re.S)
    return output


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    analysis_tables = op.create_table('shipit_dashboard_analysis',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=True),
    sa.Column('parameters', sa.Text(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    keep_existing=True
    )
    op.create_table('shipit_dashboard_bug',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('bugzilla_id', sa.Integer(), nullable=True),
    sa.Column('payload', sa.Binary(), nullable=True),
    sa.Column('payload_hash', sa.String(length=40), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('bugzilla_id')
    )
    op.create_table('shipit_dashboard_analysis_bugs',
    sa.Column('analysis_id', sa.Integer(), nullable=True),
    sa.Column('bug_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['analysis_id'], ['shipit_dashboard_analysis.id'], ),
    sa.ForeignKeyConstraint(['bug_id'], ['shipit_dashboard_bug.id'], )
    )
    ### end Alembic commands ###

    # Empty analysis
    try:
        # Postgresql
        op.execute("TRUNCATE TABLE shipit_dashboard_analysis CASCADE")
    except:
        # Sqlite
        op.execute("DELETE FROM shipit_dashboard_analysis")

    # Setup initial analysis
    all_analysis = json.load(open(os.path.join(HERE, 'analysis.json'), 'r'))
    op.bulk_insert(analysis_tables, all_analysis)


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('shipit_dashboard_analysis_bugs')
    op.drop_table('shipit_dashboard_bug')
    op.drop_table('shipit_dashboard_analysis')
    ### end Alembic commands ###
