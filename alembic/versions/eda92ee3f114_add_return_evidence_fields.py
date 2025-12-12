"""add_return_evidence_fields

Revision ID: eda92ee3f114
Revises: 7c3f8a9b2e1d
Create Date: 2025-12-12 23:36:36.620780

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eda92ee3f114'
down_revision: Union[str, None] = '7c3f8a9b2e1d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new return statuses to enum (handled by SQLAlchemy automatically)
    
    # Add evidence tracking columns
    op.add_column('orders', sa.Column('return_evidence_photos', sa.JSON(), nullable=True))
    op.add_column('orders', sa.Column('return_evidence_video', sa.String(500), nullable=True))
    op.add_column('orders', sa.Column('return_evidence_description', sa.Text(), nullable=True))
    op.add_column('orders', sa.Column('return_shipping_provider', sa.String(100), nullable=True))
    op.add_column('orders', sa.Column('return_tracking_number', sa.String(100), nullable=True))
    op.add_column('orders', sa.Column('return_shipped_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('orders', sa.Column('return_received_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('orders', sa.Column('qc_notes', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove evidence tracking columns
    op.drop_column('orders', 'qc_notes')
    op.drop_column('orders', 'return_received_at')
    op.drop_column('orders', 'return_shipped_at')
    op.drop_column('orders', 'return_tracking_number')
    op.drop_column('orders', 'return_shipping_provider')
    op.drop_column('orders', 'return_evidence_description')
    op.drop_column('orders', 'return_evidence_video')
    op.drop_column('orders', 'return_evidence_photos')
