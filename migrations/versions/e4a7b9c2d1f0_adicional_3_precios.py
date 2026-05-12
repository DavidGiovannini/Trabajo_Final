"""adicional_3_precios

Revision ID: e4a7b9c2d1f0
Revises: d3f1a2b4c890
Create Date: 2026-05-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'e4a7b9c2d1f0'
down_revision = 'd3f1a2b4c890'
branch_labels = None
depends_on = None


def upgrade():
    # Agregar los 3 campos nuevos y migrar precio → precio_base
    with op.batch_alter_table('adicional_mueble', schema=None) as batch_op:
        batch_op.add_column(sa.Column('precio_base',    sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('precio_alacena', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('precio_inox',    sa.Float(), nullable=True))

    # Copiar el precio existente a precio_base
    op.execute("UPDATE adicional_mueble SET precio_base = precio")

    # Eliminar la columna vieja
    with op.batch_alter_table('adicional_mueble', schema=None) as batch_op:
        batch_op.drop_column('precio')


def downgrade():
    with op.batch_alter_table('adicional_mueble', schema=None) as batch_op:
        batch_op.add_column(sa.Column('precio', sa.Float(), nullable=False, server_default='0'))

    op.execute("UPDATE adicional_mueble SET precio = COALESCE(precio_base, 0)")

    with op.batch_alter_table('adicional_mueble', schema=None) as batch_op:
        batch_op.drop_column('precio_inox')
        batch_op.drop_column('precio_alacena')
        batch_op.drop_column('precio_base')
