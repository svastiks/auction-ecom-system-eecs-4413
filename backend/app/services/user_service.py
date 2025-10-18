from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from fastapi import HTTPException, status
from app.models.user import User, Address
from app.schemas.user import UserUpdate
from app.schemas.address import AddressCreate, AddressUpdate
import uuid

class UserService:
    def __init__(self, db: Session):
        self.db = db

    async def get_user_profile(self, user_id: uuid.UUID) -> User:
        """Get user profile by ID."""
        stmt = select(User).where(User.user_id == user_id)
        user = self.db.execute(stmt).scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user

    async def update_user_profile(self, user_id: uuid.UUID, user_update: UserUpdate) -> User:
        """Update user profile."""
        stmt = select(User).where(User.user_id == user_id)
        user = self.db.execute(stmt).scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check if email is being changed and if it's already taken
        if user_update.email and user_update.email != user.email:
            email_stmt = select(User).where(
                and_(User.email == user_update.email, User.user_id != user_id)
            )
            existing_user = self.db.execute(email_stmt).scalar_one_or_none()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

        # Update fields
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    async def get_user_addresses(self, user_id: uuid.UUID) -> List[Address]:
        """Get all addresses for a user."""
        stmt = select(Address).where(Address.user_id == user_id).order_by(Address.created_at.desc())
        addresses = self.db.execute(stmt).scalars().all()
        return list(addresses)

    async def create_address(self, user_id: uuid.UUID, address_data: AddressCreate) -> Address:
        """Create a new address for a user."""
        # If this is set as default, unset all other defaults for this user
        if address_data.is_default_shipping:
            await self._unset_default_addresses(user_id)

        address = Address(
            user_id=user_id,
            **address_data.model_dump()
        )
        
        self.db.add(address)
        self.db.commit()
        self.db.refresh(address)
        return address

    async def update_address(self, user_id: uuid.UUID, address_id: uuid.UUID, address_update: AddressUpdate) -> Address:
        """Update an address."""
        stmt = select(Address).where(
            and_(Address.address_id == address_id, Address.user_id == user_id)
        )
        address = self.db.execute(stmt).scalar_one_or_none()
        
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )

        # If setting as default, unset other defaults
        if address_update.is_default_shipping:
            await self._unset_default_addresses(user_id, exclude_address_id=address_id)

        # Update fields
        update_data = address_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(address, field, value)

        self.db.commit()
        self.db.refresh(address)
        return address

    async def delete_address(self, user_id: uuid.UUID, address_id: uuid.UUID) -> bool:
        """Delete an address."""
        stmt = select(Address).where(
            and_(Address.address_id == address_id, Address.user_id == user_id)
        )
        address = self.db.execute(stmt).scalar_one_or_none()
        
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )

        self.db.delete(address)
        self.db.commit()
        return True

    async def _unset_default_addresses(self, user_id: uuid.UUID, exclude_address_id: Optional[uuid.UUID] = None):
        """Unset all default addresses for a user."""
        stmt = select(Address).where(Address.user_id == user_id)
        if exclude_address_id:
            stmt = stmt.where(Address.address_id != exclude_address_id)
        
        addresses = self.db.execute(stmt).scalars().all()
        for address in addresses:
            address.is_default_shipping = False
        
        self.db.commit()
