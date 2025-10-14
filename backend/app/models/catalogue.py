from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Index, Integer, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    category_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(120), unique=True, nullable=False)
    description = Column(Text)
    parent_category_id = Column(UUID(as_uuid=True), ForeignKey("categories.category_id", ondelete="SET NULL"))

    # Relationships
    parent_category = relationship("Category", remote_side=[category_id])
    subcategories = relationship("Category", back_populates="parent_category")
    catalogue_items = relationship("CatalogueItem", back_populates="category")


class CatalogueItem(Base):
    __tablename__ = "catalogue_items"

    item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.category_id"))
    keywords = Column(Text)
    base_price = Column(Numeric(12, 2), nullable=False)
    shipping_price_normal = Column(Numeric(12, 2), nullable=False)
    shipping_price_expedited = Column(Numeric(12, 2), nullable=False)
    shipping_time_days = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    seller = relationship("User", back_populates="catalogue_items")
    category = relationship("Category", back_populates="catalogue_items")
    images = relationship("ItemImage", back_populates="item", cascade="all, delete-orphan")
    auction = relationship("Auction", back_populates="item", uselist=False)
    orders = relationship("Order", back_populates="item")

    # Indexes
    __table_args__ = (
        Index('idx_items_category', 'category_id'),
        Index('idx_items_seller', 'seller_id'),
    )


class ItemImage(Base):
    __tablename__ = "item_images"

    image_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID(as_uuid=True), ForeignKey("catalogue_items.item_id", ondelete="CASCADE"), nullable=False)
    url = Column(Text, nullable=False)
    position = Column(Integer, nullable=False, default=0)

    # Relationships
    item = relationship("CatalogueItem", back_populates="images")

    # Constraints
    __table_args__ = (
        UniqueConstraint('item_id', 'position', name='uq_item_position'),
    )
