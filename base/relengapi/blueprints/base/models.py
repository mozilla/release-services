import sqlalchemy as sa

def relengapi_model(metadata):
    sa.Table('builds', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('master', sa.String(100)),
    )
    sa.Table('more_builds', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('master', sa.String(100)),
    )

def scheduler_model(metadata):
    sa.Table('builds', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('number', sa.Integer, nullable=False),
        sa.Column('brid', sa.Integer, nullable=False),
        sa.Column('start_time', sa.Integer, nullable=False),
        sa.Column('finish_time', sa.Integer),
    )
