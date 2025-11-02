from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.order import Order
from app.models.user import User
from app.schemas.order import Order as OrderSchema

router = APIRouter()


@router.get("", response_model=List[OrderSchema])
async def get_orders(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all orders for the currently logged-in user.
    
    Returns all orders where the current user is the buyer.
    """
    orders = db.query(Order).options(
        joinedload(Order.auction),
        joinedload(Order.buyer),
        joinedload(Order.item),
        joinedload(Order.shipping_address),
        joinedload(Order.payment),
        joinedload(Order.receipt),
        joinedload(Order.shipment)
    ).filter(Order.buyer_id == current_user.user_id).order_by(Order.created_at.desc()).all()
    
    return orders

