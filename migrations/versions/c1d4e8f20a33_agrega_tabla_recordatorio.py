"""agrega_tabla_recordatorio

Revision ID: c1d4e8f20a33
Revises: b7c2e1f93d11
Create Date: 2026-05-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c1d4e8f20a33'
down_revision = 'b7c2e1f93d11'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'recordatorio',
        sa.Column('id',          sa.Integer(),     nullable=False),
        sa.Column('titulo',      sa.String(200),   nullable=False),
        sa.Column('descripcion', sa.Text(),        nullable=True),
        sa.Column('fecha',       sa.Date(),        nullable=False),
        sa.Column('hora',        sa.String(5),     nullable=True),
        sa.Column('color',       sa.String(20),    nullable=False, server_default='azul'),
        sa.Column('completado',  sa.Boolean(),     nullable=False, server_default='0'),
        sa.Column('notificado',  sa.Boolean(),     nullable=False, server_default='0'),
        sa.Column('created_at',  sa.DateTime(),    nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('recordatorio')
