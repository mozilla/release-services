import sqlalchemy as sa

def init_app(app):
    metadata = app.db.meta['scheduler']
    sa.Table('builds', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('number', sa.Integer, nullable=False),
        sa.Column('brid', sa.Integer, nullable=False),
        sa.Column('start_time', sa.Integer, nullable=False),
        sa.Column('finish_time', sa.Integer),
    )
