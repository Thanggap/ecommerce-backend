"""add_return_tracking_column_to_orders

Revision ID: 7c3f8a9b2e1d
Revises: 4f9a2e1c8d5b
Create Date: 2025-12-12 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c3f8a9b2e1d'
down_revision: Union[str, None] = '4f9a2e1c8d5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add return tracking column to orders table
    op.add_column('orders', sa.Column('return_requested_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove return tracking column from orders table
    op.drop_column('orders', 'return_requested_at')
