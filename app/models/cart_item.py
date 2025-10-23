"""
CartItem Model

Defines the Pydantic model for shopping cart items.
Represents a book item in the user's shopping cart.
"""

from typing import Optional
from pydantic import BaseModel, Field


class CartItemBase(BaseModel):
    """Base cart item model with common fields."""

    title: str = Field(..., min_length=1, max_length=255, description="Book title")
    author: str = Field(..., min_length=1, max_length=255, description="Book author")
    price: float = Field(..., gt=0, description="Book price (must be greater than 0)")
    quantity: int = Field(..., gt=0, description="Quantity in cart (must be greater than 0)")
    image: Optional[str] = Field(None, description="Book cover image URL")


class CartItemCreate(CartItemBase):
    """CartItem model for adding items to cart."""

    pass


class CartItemUpdate(BaseModel):
    """CartItem model for updating cart items."""

    quantity: int = Field(..., gt=0, description="Updated quantity (must be greater than 0)")
    price: Optional[float] = Field(None, gt=0, description="Updated price (optional)")


class CartItem(CartItemBase):
    """
    Complete cart item model with metadata.

    Represents a book item in the shopping cart with all necessary information
    for display and checkout.
    """

    id: str = Field(..., description="Unique cart item identifier (Firestore document ID)")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        populate_by_name = True
