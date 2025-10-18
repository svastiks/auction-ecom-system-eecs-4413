from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class CategoryBase(BaseModel):
    name: str = Field(..., max_length=120, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    parent_category_id: Optional[UUID] = Field(
        None, description="Parent category ID for subcategories"
    )


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = None
    parent_category_id: Optional[UUID] = None


class Category(CategoryBase):
    category_id: UUID
    parent_category: Optional["Category"] = None
    subcategories: List["Category"] = []
    catalogue_items: List["CatalogueItem"] = []

    class Config:
        from_attributes = True


class ItemImageBase(BaseModel):
    url: str = Field(..., description="Image URL")
    position: int = Field(0, description="Image position/order")


class ItemImageCreate(ItemImageBase):
    pass


class ItemImage(ItemImageBase):
    image_id: UUID
    item_id: UUID

    class Config:
        from_attributes = True


class CatalogueItemBase(BaseModel):
    title: str = Field(..., max_length=200, description="Item title")
    description: Optional[str] = Field(None, description="Item description")
    category_id: Optional[UUID] = Field(None, description="Category ID")
    keywords: Optional[str] = Field(None, description="Search keywords")
    base_price: Decimal = Field(..., description="Base price of the item")
    shipping_price_normal: Decimal = Field(..., description="Normal shipping price")
    shipping_price_expedited: Decimal = Field(
        ..., description="Expedited shipping price"
    )
    shipping_time_days: int = Field(..., description="Shipping time in days")
    is_active: bool = Field(True, description="Whether item is active")


class CatalogueItemCreate(CatalogueItemBase):
    images: Optional[List[ItemImageCreate]] = Field(
        default_factory=list, description="Item images"
    )


class CatalogueItemUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    keywords: Optional[str] = None
    base_price: Optional[Decimal] = None
    shipping_price_normal: Optional[Decimal] = None
    shipping_price_expedited: Optional[Decimal] = None
    shipping_time_days: Optional[int] = None
    is_active: Optional[bool] = None


class CatalogueItem(CatalogueItemBase):
    item_id: UUID
    seller_id: UUID
    created_at: datetime
    updated_at: datetime
    seller: Optional["UserRef"] = None
    category: Optional[Category] = None
    images: List[ItemImage] = []
    auction: Optional["Auction"] = None

    class Config:
        from_attributes = True