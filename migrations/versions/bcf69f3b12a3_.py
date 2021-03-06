"""empty message

Revision ID: bcf69f3b12a3
Revises: c8af99d57b6b
Create Date: 2022-06-06 02:14:48.179008

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bcf69f3b12a3'
down_revision = 'c8af99d57b6b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('match', sa.Column('slip_id', sa.Integer(), nullable=True))
    op.drop_constraint('match_bet_id_fkey', 'match', type_='foreignkey')
    op.create_foreign_key(None, 'match', 'bet', ['bet_id'], ['id'])
    op.create_foreign_key(None, 'match', 'slip', ['slip_id'], ['id'])
    op.add_column('team', sa.Column('teamatt_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'team', 'teamatt', ['teamatt_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'team', type_='foreignkey')
    op.drop_column('team', 'teamatt_id')
    op.drop_constraint(None, 'match', type_='foreignkey')
    op.drop_constraint(None, 'match', type_='foreignkey')
    op.create_foreign_key('match_bet_id_fkey', 'match', 'slip', ['bet_id'], ['id'])
    op.drop_column('match', 'slip_id')
    # ### end Alembic commands ###
