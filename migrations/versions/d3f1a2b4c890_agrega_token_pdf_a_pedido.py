"""agrega_token_pdf_a_pedido

Revision ID: d3f1a2b4c890
Revises: c1d4e8f20a33
Create Date: 2026-05-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'd3f1a2b4c890'
down_revision = 'c1d4e8f20a33'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('pedido', schema=None) as batch_op:
        batch_op.add_column(sa.Column('token_pdf', sa.String(32), nullable=True))
        batch_op.create_unique_constraint('uq_pedido_token_pdf', ['token_pdf'])


def downgrade():
    with op.batch_alter_table('pedido', schema=None) as batch_op:
        batch_op.drop_constraint('uq_pedido_token_pdf', type_='unique')
        batch_op.drop_column('token_pdf')
