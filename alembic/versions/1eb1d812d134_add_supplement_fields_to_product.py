"""add_supplement_fields_to_product

Revision ID: 1eb1d812d134
Revises: add_product_colors
Create Date: 2025-12-10 21:35:57.943628

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1eb1d812d134'
down_revision: Union[str, None] = '6a4d266ee151'  # Skip add_product_colors since we're dropping that table
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add supplement-specific fields to products table
    op.add_column('products', sa.Column('serving_size', sa.String(100), nullable=True))
    op.add_column('products', sa.Column('servings_per_container', sa.Integer(), nullable=True))
    op.add_column('products', sa.Column('ingredients', sa.Text(), nullable=True))
    op.add_column('products', sa.Column('allergen_info', sa.Text(), nullable=True))
    op.add_column('products', sa.Column('usage_instructions', sa.Text(), nullable=True))
    op.add_column('products', sa.Column('warnings', sa.Text(), nullable=True))
    op.add_column('products', sa.Column('expiry_date', sa.Date(), nullable=True))
    op.add_column('products', sa.Column('manufacturer', sa.String(255), nullable=True))
    op.add_column('products', sa.Column('country_of_origin', sa.String(100), nullable=True))
    op.add_column('products', sa.Column('certification', sa.String(255), nullable=True))
    
    # Drop product_colors table if exists (not relevant for supplements)
    # Using raw SQL to handle "IF EXISTS"
    op.execute('DROP TABLE IF EXISTS product_colors CASCADE')


def downgrade() -> None:
    # Recreate product_colors table
    op.create_table(
        'product_colors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('color', sa.String(), nullable=False),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'])
    )
    
    # Remove supplement fields
    op.drop_column('products', 'certification')
    op.drop_column('products', 'country_of_origin')
    op.drop_column('products', 'manufacturer')
    op.drop_column('products', 'expiry_date')
    op.drop_column('products', 'warnings')
    op.drop_column('products', 'usage_instructions')
    op.drop_column('products', 'allergen_info')
    op.drop_column('products', 'ingredients')
    op.drop_column('products', 'servings_per_container')
    op.drop_column('products', 'serving_size')
