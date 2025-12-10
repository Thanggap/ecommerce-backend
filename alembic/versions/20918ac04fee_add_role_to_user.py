"""add_role_to_user

Revision ID: 20918ac04fee
Revises: 028376dab2f8
Create Date: 2025-12-05 02:31:22.139517

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20918ac04fee'
down_revision: Union[str, None] = '028376dab2f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('role', sa.String(), nullable=False, server_default='user'))


def downgrade() -> None:
    op.drop_column('users', 'role')
