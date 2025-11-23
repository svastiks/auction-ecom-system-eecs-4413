"""
Orders endpoints for UC4/UC5/UC6: Pay Now, payment capture, receipt and shipment.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.order import Order, Payment, Receipt, Shipment
from app.models.auction import Auction, Bid
from app.models.catalogue import CatalogueItem
from app.models.user import User, Address
from app.schemas.order import (
    OrderResponse,
    OrderDetail,
    OrderCreate,
    PaymentRequest,
    PaymentResponse,
    ReceiptResponse,
    ShipmentResponse,
    ShippingMethodUpdate,
    PayResponse,
    ShippingMethod,
    OrderStatus as OrderStatusEnum,
    PaymentStatus,
)
from app.schemas.auction import AuctionStatus
from app.services.payment_service import PaymentService

router = APIRouter()


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create an order for a completed auction.
    Only the winning bidder can create an order.
    This endpoint creates an order in PENDING_PAYMENT status.
    """
    # Get auction
    auction = db.query(Auction).options(
        joinedload(Auction.item)
    ).filter(Auction.auction_id == order_data.auction_id).first()
    
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    # Check if auction has ended
    if auction.status != AuctionStatus.ENDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create order for an auction that hasn't ended"
        )
    
    # Check if order already exists for this auction
    existing_order = db.query(Order).filter(
        Order.auction_id == order_data.auction_id
    ).first()
    
    if existing_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order already exists for this auction"
        )
    
    # Verify shipping address belongs to user
    address = db.query(Address).filter(
        Address.address_id == order_data.shipping_address_id,
        Address.user_id == current_user.user_id
    ).first()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipping address not found or does not belong to you"
        )
    
    # Get winning bid amount
    winning_bid = db.query(Bid).filter(
        Bid.bid_id == auction.winning_bid_id
    ).first()
    
    if not winning_bid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Winning bid not found"
        )
    
    winning_bid_amount = winning_bid.amount
    
    # Calculate shipping cost and total
    shipping_cost, total_amount = PaymentService.calculate_total(
        winning_bid_amount=winning_bid_amount,
        shipping_method=order_data.shipping_method.value,
        shipping_cost_normal=auction.item.shipping_price_normal,
        shipping_cost_expedited=auction.item.shipping_price_expedited
    )
    
    # Create order
    order = Order(
        auction_id=order_data.auction_id,
        buyer_id=auction.winning_bidder_id,
        item_id=auction.item_id,
        winning_bid_amount=winning_bid_amount,
        shipping_method=order_data.shipping_method.value,
        shipping_cost=shipping_cost,
        total_amount=total_amount,
        shipping_address_id=order_data.shipping_address_id,
        status=OrderStatusEnum.PENDING_PAYMENT.value
    )
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return order


@router.get("/{order_id}", response_model=OrderDetail)
async def get_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    UC4/UC5/UC6: Get order details including payment, receipt, and shipment information.
    Only the buyer can view their own order.
    """
    order = db.query(Order).options(
        joinedload(Order.payment),
        joinedload(Order.receipt),
        joinedload(Order.shipment),
        joinedload(Order.auction),
        joinedload(Order.item)
    ).filter(Order.order_id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Only buyer can view their order
    if order.buyer_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own orders"
        )
    
    return order


@router.put("/{order_id}/shipping-method", response_model=OrderResponse)
async def update_shipping_method(
    order_id: UUID,
    shipping_update: ShippingMethodUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    UC4: Update shipping method for an order and recalculate total.
    Only the buyer can update shipping method.
    Order must be in PENDING_PAYMENT status.
    """
    order = db.query(Order).options(
        joinedload(Order.item)
    ).filter(Order.order_id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Only buyer can update
    if order.buyer_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own orders"
        )
    
        # Can only update if payment hasn't been made
        if order.status != OrderStatusEnum.PENDING_PAYMENT.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update shipping method for order with status {order.status}"
            )
    
    # Recalculate shipping cost and total
    shipping_cost, total_amount = PaymentService.calculate_total(
        winning_bid_amount=order.winning_bid_amount,
        shipping_method=shipping_update.shipping_method.value,
        shipping_cost_normal=order.item.shipping_price_normal,
        shipping_cost_expedited=order.item.shipping_price_expedited
    )
    
    order.shipping_method = shipping_update.shipping_method.value
    order.shipping_cost = shipping_cost
    order.total_amount = total_amount
    
    db.commit()
    db.refresh(order)
    
    return order


@router.post("/{order_id}/pay", response_model=PayResponse)
async def pay_order(
    order_id: UUID,
    payment_request: PaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    UC4: Pay for an order.
    Only the winning bidder can pay.
    On success: payment.status=CAPTURED, order.status=PAID, receipt issued, shipment created.
    Failure simulation: card number starting with "4000" fails.
    """
    order = db.query(Order).options(
        joinedload(Order.auction),
        joinedload(Order.item)
    ).filter(Order.order_id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check if user is the winning bidder
    if order.buyer_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the winning bidder can pay for this order"
        )
    
    # Check if auction has ended and has a winner
    if order.auction.status != AuctionStatus.ENDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot pay for order from an auction that hasn't ended"
        )
    
    if order.auction.winning_bidder_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are not the winning bidder for this auction"
        )
    
    # Check order status
    if order.status == OrderStatusEnum.PAID.value:
        # Check if payment already exists and is successful (idempotency)
        existing_payment = db.query(Payment).filter(
            Payment.order_id == order.order_id,
            Payment.status == PaymentStatus.CAPTURED.value
        ).first()
        
        if existing_payment:
            return PayResponse(
                order_id=order.order_id,
                payment_id=existing_payment.payment_id,
                status=existing_payment.status,
                message="Payment already processed successfully",
                total_amount=order.total_amount
            )
    
    if order.status not in [OrderStatusEnum.PENDING_PAYMENT.value, OrderStatusEnum.FAILED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot pay for order with status {order.status}"
        )
    
    # Process payment
    payment, success, failure_reason = PaymentService.process_payment(
        db=db,
        order=order,
        payment_request=payment_request
    )
    
    if not success:
        # Payment failed - order and payment status already updated by service
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=failure_reason or "Payment failed"
        )
    
    # Payment successful - create receipt and shipment
    # Create receipt
    if not order.receipt:
        receipt_number = f"RCP-{datetime.now().strftime('%Y%m%d')}-{str(order.order_id)[:8].upper()}"
        receipt = Receipt(
            order_id=order.order_id,
            receipt_number=receipt_number,
            total_paid=order.total_amount,
            notes=f"Payment for order {order.order_id}"
        )
        db.add(receipt)
        db.flush()
    
    # Create shipment
    if not order.shipment:
        shipment = Shipment(
            order_id=order.order_id,
            estimated_days=order.item.shipping_time_days,
            status="PENDING"
        )
        db.add(shipment)
        db.flush()
    
    db.commit()
    db.refresh(payment)
    
    return PayResponse(
        order_id=order.order_id,
        payment_id=payment.payment_id,
        status=payment.status,
        message="Payment processed successfully",
        total_amount=order.total_amount
    )


@router.get("/{order_id}/receipt", response_model=ReceiptResponse)
async def get_receipt(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    UC5: Get receipt for an order.
    Only the buyer can view their receipt.
    """
    order = db.query(Order).filter(Order.order_id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Only buyer can view
    if order.buyer_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view receipts for your own orders"
        )
    
    receipt = db.query(Receipt).filter(Receipt.order_id == order_id).first()
    
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found. Order may not be paid yet."
        )
    
    return receipt


@router.get("/{order_id}/shipment", response_model=ShipmentResponse)
async def get_shipment(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    UC6: Get shipment information for an order.
    Only the buyer can view their shipment.
    """
    order = db.query(Order).filter(Order.order_id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Only buyer can view
    if order.buyer_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view shipments for your own orders"
        )
    
    shipment = db.query(Shipment).filter(Shipment.order_id == order_id).first()
    
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found. Order may not be paid yet."
        )
    
    return shipment

