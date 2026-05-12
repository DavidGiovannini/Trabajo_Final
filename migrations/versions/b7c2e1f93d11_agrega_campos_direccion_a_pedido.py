"""agrega_campos_direccion_a_pedido

Revision ID: b7c2e1f93d11
Revises: a3c1d7e82f90
Create Date: 2026-05-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b7c2e1f93d11'
down_revision = 'a3c1d7e82f90'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('pedido', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pais',          sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('localidad',     sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('codigo_postal', sa.String(20),  nullable=True))
        batch_op.add_column(sa.Column('barrio',        sa.String(100), nullable=True))


def downgrade():
    with op.batch_alter_table('pedido', schema=None) as batch_op:
        batch_op.drop_column('barrio')
        batch_op.drop_column('codigo_postal')
        batch_op.drop_column('localidad')
        batch_op.drop_column('pais')
