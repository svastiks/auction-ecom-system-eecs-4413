"""
Payment service with DUMMY gateway simulation.
Simulates payment processing for the auction system.
"""
from decimal import Decimal
from typing import Tuple, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.order import Payment, Order
from app.schemas.order import PaymentRequest, PaymentStatus, OrderStatus


class PaymentService:
    """Service for handling payment processing with DUMMY gateway."""

    PROCESSOR_NAME = "DUMMY"

    @staticmethod
    def process_payment(
        db: Session,
        order: Order,
        payment_request: PaymentRequest
    ) -> Tuple[Payment, bool, Optional[str]]:
        """
        Process payment through DUMMY gateway.
        
        Args:
            db: Database session
            order: Order to process payment for
            payment_request: Payment request with card details
            
        Returns:
            Tuple of (Payment object, success: bool, failure_reason: Optional[str])
            
        Failure simulation:
            - Card number starting with "4000" will fail
            - All other card numbers will succeed
        """
        # Check if payment already exists for this order
        existing_payment = db.query(Payment).filter(
            Payment.order_id == order.order_id
        ).first()
        
        if existing_payment:
            # Idempotency: if payment already exists and is successful, return it
            if existing_payment.status == PaymentStatus.CAPTURED.value:
                return existing_payment, True, None
            # If it failed, allow retry by creating a new payment record
            # (or we could update existing - for now, we'll allow new payment)
        
        # Determine if payment should fail based on card number
        should_fail = payment_request.card_number.startswith("4000")
        
        # Create payment record
        payment = Payment(
            order_id=order.order_id,
            amount=order.total_amount,
            currency="USD",
            status=PaymentStatus.INITIATED.value,
            processor=PaymentService.PROCESSOR_NAME,
            processor_txn_id=str(uuid4()) if not should_fail else None
        )
        
        db.add(payment)
        db.flush()  # Flush to get payment_id
        
        if should_fail:
            # Simulate payment failure
            payment.status = PaymentStatus.FAILED.value
            payment.failure_reason = "Card declined by payment processor"
            order.status = OrderStatus.FAILED.value
            
            db.commit()
            return payment, False, payment.failure_reason
        
        # Simulate successful payment
        # In real system, we'd make API call here
        payment.status = PaymentStatus.CAPTURED.value
        order.status = OrderStatus.PAID.value
        
        db.commit()
        
        return payment, True, None

    @staticmethod
    def calculate_total(
        winning_bid_amount: Decimal,
        shipping_method: str,
        shipping_cost_normal: Decimal,
        shipping_cost_expedited: Decimal
    ) -> Tuple[Decimal, Decimal]:
        """
        Calculate shipping cost and total amount.
        
        Args:
            winning_bid_amount: Amount of the winning bid
            shipping_method: "NORMAL" or "EXPEDITED"
            shipping_cost_normal: Normal shipping cost
            shipping_cost_expedited: Expedited shipping cost
            
        Returns:
            Tuple of (shipping_cost, total_amount)
        """
        if shipping_method == "EXPEDITED":
            shipping_cost = shipping_cost_expedited
        else:
            shipping_cost = shipping_cost_normal
        
        total_amount = winning_bid_amount + shipping_cost
        
        return shipping_cost, total_amount

