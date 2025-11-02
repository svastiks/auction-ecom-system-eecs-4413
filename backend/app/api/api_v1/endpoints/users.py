from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.services.user_service import UserService
from app.services.bid_service import BidService
from app.schemas.user import UserUpdate, UserResponse
from app.schemas.address import AddressCreate, AddressUpdate, AddressResponse, AddressListResponse
from app.schemas.bid import MyBidsResponse
from app.models.user import User

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's profile information.
    """
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile information.
    
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **phone**: Phone number
    - **email**: Email address (must be unique)
    """
    user_service = UserService(db)
    updated_user = await user_service.update_user_profile(current_user.user_id, user_update)
    return updated_user

@router.get("/me/addresses", response_model=AddressListResponse)
async def get_user_addresses(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all addresses for the current user.
    """
    user_service = UserService(db)
    addresses = await user_service.get_user_addresses(current_user.user_id)
    
    return AddressListResponse(
        addresses=addresses,
        total=len(addresses)
    )

@router.post("/me/addresses", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user_address(
    address_data: AddressCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new address for the current user.
    
    - **street_line1**: Street address line 1
    - **street_line2**: Street address line 2 (optional)
    - **city**: City
    - **state_region**: State or region (optional)
    - **postal_code**: Postal code/ZIP (validated format)
    - **country**: Country
    - **phone**: Phone number for this address (optional, validated format)
    - **is_default_shipping**: Set as default shipping address
    
    **Alternate A1**: Invalid fields will return validation errors with details.
    **Alternate A2**: If set as default, previous default addresses are automatically unset.
    
    Returns confirmation message: "The shipping address has been updated."
    """
    user_service = UserService(db)
    address = await user_service.create_address(current_user.user_id, address_data)
    return {
        "message": "The shipping address has been updated.",
        "address": address
    }

@router.put("/me/addresses/{address_id}", response_model=dict)
async def update_user_address(
    address_id: str,
    address_update: AddressUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing address for the current user.
    
    - **address_id**: Address ID to update
    - **street_line1**: Street address line 1
    - **street_line2**: Street address line 2 (optional)
    - **city**: City
    - **state_region**: State or region (optional)
    - **postal_code**: Postal code/ZIP (validated format)
    - **country**: Country
    - **phone**: Phone number for this address (optional, validated format)
    - **is_default_shipping**: Set as default shipping address
    
    **Alternate A1**: Invalid fields will return validation errors with details.
    **Alternate A2**: If set as default, previous default addresses are automatically unset.
    
    Returns confirmation message: "The shipping address has been updated."
    """
    user_service = UserService(db)
    address = await user_service.update_address(current_user.user_id, address_id, address_update)
    return {
        "message": "The shipping address has been updated.",
        "address": address
    }

@router.delete("/me/addresses/{address_id}", response_model=dict)
async def delete_user_address(
    address_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete an address for the current user.
    
    - **address_id**: Address ID to delete
    """
    user_service = UserService(db)
    await user_service.delete_address(current_user.user_id, address_id)
    return {"message": "Address deleted successfully"}

@router.get("/me/bids", response_model=MyBidsResponse)
async def get_my_bids(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all bids for the current user with status information.
    
    Returns a paginated list of bids with:
    - Item title
    - Last bid amount
    - Current highest bid
    - Time left (if auction is active)
    - Status: LEADING (user's bid is highest), OUTBID (user has been outbid), ENDED (auction ended), WON (user won)
    
    **Alternate A1**: If user has no bids, returns empty list with total=0.
    **Alternate A2**: Ended auctions show status ENDED with auction end time.
    """
    bid_service = BidService(db)
    bids_response = await bid_service.get_my_bids(current_user.user_id, page=page, page_size=page_size)
    return bids_response
