"""Initial: create tickets table

Revision ID: 001
Revises:
Create Date: 2025-08-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'tickets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=50), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('suggested_response', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tickets_id'), 'tickets', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tickets_id'), table_name='tickets')
    op.drop_table('tickets')
