from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.catalogue import Category, CatalogueItem, ItemImage
from app.schemas.catalogue import (
    CategoryRead,
    CategoryCreate,
    CategoryUpdate,
    CatalogueItemRead,
    CatalogueItemCreate,
    CatalogueItemUpdate,
    ItemImage as ItemImageSchema,
    ItemImageCreate,
)

router = APIRouter()

@router.get("/categories", response_model=List[CategoryRead])
def get_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    parent_id: Optional[UUID] = Query(None, description="Filter by parent category ID"),
    db: Session = Depends(get_db),
):
    query = db.query(Category)
    if parent_id is not None:
        query = query.filter(Category.parent_category_id == parent_id)

    categories = query.offset(skip).limit(limit).all()
    return categories


@router.get("/categories/{category_id}", response_model=CategoryRead)
def get_category(category_id: UUID, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post("/categories", response_model=CategoryRead)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    if category.parent_category_id:
        parent = (
            db.query(Category)
            .filter(Category.category_id == category.parent_category_id)
            .first()
        )
        if not parent:
            raise HTTPException(status_code=400, detail="Parent category not found")

    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category name already exists")

    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.put("/categories/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: UUID,
    category_update: CategoryUpdate,
    db: Session = Depends(get_db),
):
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if category_update.name and category_update.name != category.name:
        existing = (
            db.query(Category)
            .filter(
                and_(
                    Category.name == category_update.name,
                    Category.category_id != category_id,
                )
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Category name already exists")

    if category_update.parent_category_id:
        parent = (
            db.query(Category)
            .filter(Category.category_id == category_update.parent_category_id)
            .first()
        )
        if not parent:
            raise HTTPException(status_code=400, detail="Parent category not found")

    update_data = category_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category

@router.delete("/categories/{category_id}")
def delete_category(category_id: UUID, db: Session = Depends(get_db)):
    """Delete a category (only if it has no subcategories or items)"""
    category = db.query(Category).filter(Category.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if category has subcategories
    subcategories = db.query(Category).filter(Category.parent_category_id == category_id).count()
    if subcategories > 0:
        raise HTTPException(status_code=400, detail="Cannot delete category with subcategories")
    
    # Check if category has items
    items = db.query(CatalogueItem).filter(CatalogueItem.category_id == category_id).count()
    if items > 0:
        raise HTTPException(status_code=400, detail="Cannot delete category with items")
    
    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}

@router.get("/items", response_model=List[CatalogueItemRead])
def get_catalogue_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category_id: Optional[UUID] = Query(None, description="Filter by category ID"),
    seller_id: Optional[UUID] = Query(None, description="Filter by seller ID"),
    search: Optional[str] = Query(None, description="Search in title, description, and keywords"),
    active_only: bool = Query(True, description="Show only active items"),
    db: Session = Depends(get_db),
):
    query = db.query(CatalogueItem).options(
        joinedload(CatalogueItem.category),
        joinedload(CatalogueItem.seller),
        joinedload(CatalogueItem.images),
    )

    if category_id:
        query = query.filter(CatalogueItem.category_id == category_id)
    if seller_id:
        query = query.filter(CatalogueItem.seller_id == seller_id)
    if active_only:
        query = query.filter(CatalogueItem.is_active.is_(True))

    if search:
        query = query.filter(
            or_(
                CatalogueItem.title.ilike(f"%{search}%"),
                CatalogueItem.description.ilike(f"%{search}%"),
                CatalogueItem.keywords.ilike(f"%{search}%"),
            )
        )

    items = query.offset(skip).limit(limit).all()
    return items

@router.post("/items", response_model=CatalogueItemRead)
def create_catalogue_item(
    item: CatalogueItemCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new catalogue item"""
    # Check if category exists if specified
    if item.category_id:
        category = db.query(Category).filter(Category.category_id == item.category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
    
    # Create the item with seller_id from current user
    item_data = item.dict(exclude={'images'})
    item_data['seller_id'] = current_user.user_id
    db_item = CatalogueItem(**item_data)
    db.add(db_item)
    db.flush()  # Get the item_id
    
    # Add images if provided
    if item.images:
        for image_data in item.images:
            image = ItemImage(**image_data.dict(), item_id=db_item.item_id)
            db.add(image)
    
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/items/{item_id}", response_model=CatalogueItemRead)
def update_catalogue_item(
    item_id: UUID,
    item_update: CatalogueItemUpdate,
    db: Session = Depends(get_db)
):
    """Update a catalogue item"""
    item = db.query(CatalogueItem).filter(CatalogueItem.item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Catalogue item not found")
    
    # Check if category exists if specified
    if item_update.category_id:
        category = db.query(Category).filter(Category.category_id == item_update.category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
    
    update_data = item_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    db.commit()
    db.refresh(item)
    return item

@router.delete("/items/{item_id}")
def delete_catalogue_item(item_id: UUID, db: Session = Depends(get_db)):
    """Delete a catalogue item"""
    item = db.query(CatalogueItem).filter(CatalogueItem.item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Catalogue item not found")
    
    db.delete(item)
    db.commit()
    return {"message": "Catalogue item deleted successfully"}

# Image endpoints
@router.post("/items/{item_id}/images", response_model=ItemImageSchema)
def add_item_image(
    item_id: UUID,
    image: ItemImageCreate,
    db: Session = Depends(get_db)
):
    """Add an image to a catalogue item"""
    # Check if item exists
    item = db.query(CatalogueItem).filter(CatalogueItem.item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Catalogue item not found")
    
    db_image = ItemImage(**image.dict(), item_id=item_id)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

@router.delete("/images/{image_id}")
def delete_item_image(image_id: UUID, db: Session = Depends(get_db)):
    """Delete an item image"""
    image = db.query(ItemImage).filter(ItemImage.image_id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    db.delete(image)
    db.commit()
    return {"message": "Image deleted successfully"}

@router.get("/items/{item_id}", response_model=CatalogueItemRead)
def get_catalogue_item(item_id: UUID, db: Session = Depends(get_db)):
    item = (
        db.query(CatalogueItem)
        .options(
            joinedload(CatalogueItem.category),
            joinedload(CatalogueItem.seller),
            joinedload(CatalogueItem.images),
        )
        .filter(CatalogueItem.item_id == item_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Catalogue item not found")
    return item

    