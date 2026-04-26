"""agrega_producto_id_a_pedido_item

Revision ID: 1eafdacf6055
Revises: 6f9e8a2eae05
Create Date: 2026-04-26 11:02:45.704166

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1eafdacf6055'
down_revision = '6f9e8a2eae05'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('pedido_item', schema=None) as batch_op:
        batch_op.add_column(sa.Column('producto_id', sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table('pedido_item', schema=None) as batch_op:
        batch_op.drop_column('producto_id')
