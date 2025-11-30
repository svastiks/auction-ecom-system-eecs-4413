"""add_auction_id_to_catalogue_items

Revision ID: 7b59a4fb344a
Revises: 75b032319f67
Create Date: 2025-11-29 23:28:01.572895

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b59a4fb344a'
down_revision: Union[str, None] = '75b032319f67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add auction_id column to catalogue_items table
    op.add_column('catalogue_items', sa.Column('auction_id', sa.UUID(), nullable=True))
    
    # Backfill auction_id for existing items that have auctions
    op.execute("""
        UPDATE catalogue_items
        SET auction_id = auctions.auction_id
        FROM auctions
        WHERE catalogue_items.item_id = auctions.item_id
    """)
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_catalogue_items_auction_id',
        'catalogue_items',
        'auctions',
        ['auction_id'],
        ['auction_id'],
        ondelete='SET NULL'
    )
    # Add index for better query performance
    op.create_index('idx_catalogue_items_auction_id', 'catalogue_items', ['auction_id'], unique=False)


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_catalogue_items_auction_id', table_name='catalogue_items')
    # Drop foreign key constraint
    op.drop_constraint('fk_catalogue_items_auction_id', 'catalogue_items', type_='foreignkey')
    # Drop column
    op.drop_column('catalogue_items', 'auction_id')
