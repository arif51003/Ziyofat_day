"""add ingredient cost_price

Revision ID: 3d0a954ea1a7
Revises: ee756c79a93b
Create Date: 2026-08-14 15:26:01.872969

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3d0a954ea1a7'
down_revision: Union[str, Sequence[str], None] = 'ee756c79a93b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'ingredients',
        sa.Column('cost_price', sa.BigInteger(), nullable=False, server_default='0'),
    )
    op.alter_column('ingredients', 'cost_price', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('ingredients', 'cost_price')
