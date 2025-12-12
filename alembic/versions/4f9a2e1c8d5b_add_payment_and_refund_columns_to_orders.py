"""add_payment_and_refund_columns_to_orders

Revision ID: 4f9a2e1c8d5b
Revises: 20918ac04fee
Create Date: 2025-12-11 01:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f9a2e1c8d5b'
down_revision: Union[str, None] = '1eb1d812d134'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add payment and refund tracking columns to orders table
    op.add_column('orders', sa.Column('payment_intent_id', sa.String(), nullable=True))
    op.add_column('orders', sa.Column('refund_id', sa.String(), nullable=True))
    op.add_column('orders', sa.Column('refund_amount', sa.Numeric(10, 2), nullable=True))
    op.add_column('orders', sa.Column('refund_reason', sa.String(), nullable=True))
    op.add_column('orders', sa.Column('refunded_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove payment and refund columns from orders table
    op.drop_column('orders', 'refunded_at')
    op.drop_column('orders', 'refund_reason')
    op.drop_column('orders', 'refund_amount')
    op.drop_column('orders', 'refund_id')
    op.drop_column('orders', 'payment_intent_id')
