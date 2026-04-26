"""agrega_stock_descontado_a_pedido

Revision ID: a3c1d7e82f90
Revises: 1eafdacf6055
Create Date: 2026-04-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a3c1d7e82f90'
down_revision = '1eafdacf6055'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('pedido', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stock_descontado', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    with op.batch_alter_table('pedido', schema=None) as batch_op:
        batch_op.drop_column('stock_descontado')
