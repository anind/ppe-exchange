"""empty message

<<<<<<< HEAD:migrations/versions/4131a75cb8fd_.py
Revision ID: 4131a75cb8fd
Revises: 
Create Date: 2020-04-21 21:26:29.199631
=======
Revision ID: b5d77f1cb86b
Revises: 
Create Date: 2020-04-19 14:23:06.339199
>>>>>>> master:migrations/versions/b5d77f1cb86b_.py

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
<<<<<<< HEAD:migrations/versions/4131a75cb8fd_.py
revision = '4131a75cb8fd'
=======
revision = 'b5d77f1cb86b'
>>>>>>> master:migrations/versions/b5d77f1cb86b_.py
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('exchanges',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_timestamp', sa.DateTime(), nullable=True),
    sa.Column('updated_timestamp', sa.DateTime(), nullable=True),
    sa.Column('status', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('hospital',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('contact', sa.String(length=140), nullable=True),
    sa.Column('street', sa.String(length=128), nullable=True),
    sa.Column('city', sa.String(length=128), nullable=True),
    sa.Column('state', sa.String(length=128), nullable=True),
    sa.Column('zipcode', sa.String(length=128), nullable=True),
    sa.Column('name', sa.String(length=140), nullable=True),
    sa.Column('credit', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('ppe',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('sku', sa.String(length=16), nullable=True),
    sa.Column('desc', sa.String(length=200), nullable=True),
    sa.Column('img', sa.BLOB(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ppe_sku'), 'ppe', ['sku'], unique=False)
    op.create_table('exchange',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('create_timestamp', sa.DateTime(), nullable=True),
    sa.Column('updated_timestamp', sa.DateTime(), nullable=True),
    sa.Column('exchange_id', sa.Integer(), nullable=True),
    sa.Column('hospital1', sa.Integer(), nullable=True),
    sa.Column('hospital1_accept', sa.Integer(), nullable=True),
    sa.Column('hospital2', sa.Integer(), nullable=True),
    sa.Column('hospital2_accept', sa.Integer(), nullable=True),
    sa.Column('ppe', sa.Integer(), nullable=True),
    sa.Column('count', sa.Integer(), nullable=True),
    sa.Column('status', sa.Integer(), nullable=True),
    sa.Column('is_h1_verified', sa.Boolean(), nullable=True),
    sa.Column('is_h2_verified', sa.Boolean(), nullable=True),
    sa.Column('is_h1_shipped', sa.Boolean(), nullable=True),
    sa.Column('is_h2_received', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['exchange_id'], ['exchanges.id'], ),
    sa.ForeignKeyConstraint(['hospital1'], ['hospital.id'], ),
    sa.ForeignKeyConstraint(['ppe'], ['ppe.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('has',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('hospital_id', sa.Integer(), nullable=True),
    sa.Column('ppe_id', sa.Integer(), nullable=True),
    sa.Column('count', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['hospital_id'], ['hospital.id'], ),
    sa.ForeignKeyConstraint(['ppe_id'], ['ppe.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('is_admin', sa.Boolean(), nullable=True),
    sa.Column('is_verified', sa.Boolean(), nullable=True),
    sa.Column('verification_key', sa.String(length=128), nullable=True),
    sa.Column('hospital_contact', sa.String(length=128), nullable=True),
    sa.Column('hospital_id', sa.Integer(), nullable=True),
    sa.Column('hospital_street', sa.String(length=128), nullable=True),
    sa.Column('hospital_city', sa.String(length=128), nullable=True),
    sa.Column('hospital_state', sa.String(length=128), nullable=True),
    sa.Column('hospital_zipcode', sa.String(length=128), nullable=True),
    sa.ForeignKeyConstraint(['hospital_id'], ['hospital.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    op.create_table('wants',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('hospital_id', sa.Integer(), nullable=True),
    sa.Column('ppe_id', sa.Integer(), nullable=True),
    sa.Column('count', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['hospital_id'], ['hospital.id'], ),
    sa.ForeignKeyConstraint(['ppe_id'], ['ppe.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('wants')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    op.drop_table('has')
    op.drop_table('exchange')
    op.drop_index(op.f('ix_ppe_sku'), table_name='ppe')
    op.drop_table('ppe')
    op.drop_table('hospital')
    op.drop_table('exchanges')
    # ### end Alembic commands ###
