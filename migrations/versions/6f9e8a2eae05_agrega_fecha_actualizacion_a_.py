"""refactor producto: tipo+stock, quita material+por_metro

Revision ID: 6f9e8a2eae05
Revises:
Create Date: 2026-04-22 20:00:05.570555

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6f9e8a2eae05'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('producto', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tipo', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('stock', sa.Integer(), nullable=True))
        batch_op.drop_column('por_metro')
        batch_op.drop_column('material')


def downgrade():
    with op.batch_alter_table('producto', schema=None) as batch_op:
        batch_op.add_column(sa.Column('material', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('por_metro', sa.Boolean(), nullable=True))
        batch_op.drop_column('stock')
        batch_op.drop_column('tipo')
