"""
Payment Model

Defines the Pydantic models for payment history and PayPal order information.
Aligned with the client-side PayPal interfaces from Next.js application.
"""

from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class PaymentItemBase(BaseModel):
    """Base model for a payment item (book being purchased)."""

    book_id: str = Field(..., description="ID of the book being purchased")
    book_title: str = Field(..., description="Title of the book")
    price: float = Field(..., gt=0, description="Price per unit")
    currency: str = Field(default="USD", max_length=3, description="Currency code (ISO 4217)")
    quantity: int = Field(..., gt=0, description="Quantity being purchased")


class PaymentItem(PaymentItemBase):
    """
    Complete payment item model.

    Represents a single item (book) in a payment order.
    """

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        populate_by_name = True


class PaymentHistoryBase(BaseModel):
    """Base payment history model with common fields."""

    # PayPal Order Information
    paypal_order_id: str = Field(..., description="PayPal order ID")
    status: Literal["created", "approved", "completed", "failed", "cancelled"] = Field(
        ..., description="Payment status"
    )

    # User Information
    user_id: Optional[str] = Field(None, description="User ID (if authenticated)")
    payer_email: Optional[EmailStr] = Field(None, description="Payer's email address")

    # Order Details
    items: List[PaymentItem] = Field(..., description="List of items purchased")
    currency_code: str = Field(default="USD", max_length=3, description="Currency code")
    total_amount: float = Field(..., gt=0, description="Total order amount")

    # Reference Information
    reference_id: Optional[str] = Field(None, description="Custom reference ID")

    # Additional Metadata
    notes: Optional[str] = Field(None, description="Additional notes or metadata")


class PaymentHistoryCreate(PaymentHistoryBase):
    """Payment history model for creating new payment records."""

    pass


class PaymentHistoryUpdate(BaseModel):
    """Payment history model for updating existing payment records."""

    status: Optional[
        Literal["created", "approved", "completed", "failed", "cancelled"]
    ] = Field(None, description="Payment status")
    payer_email: Optional[EmailStr] = Field(None, description="Payer's email address")
    notes: Optional[str] = Field(None, description="Additional notes")


class PaymentHistory(PaymentHistoryBase):
    """
    Complete payment history model with metadata.

    Represents a payment record stored in the payment_history collection.
    """

    id: str = Field(..., description="Unique payment record identifier (Firestore document ID)")
    created_at: datetime = Field(..., description="Payment record creation timestamp")
    updated_at: datetime = Field(..., description="Payment record last update timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        populate_by_name = True


# Client-facing response models


class PaymentOrderResponse(BaseModel):
    """Response returned after creating a payment order record."""

    id: str = Field(..., description="Payment record ID")
    paypal_order_id: str = Field(..., description="PayPal order ID")
    status: str = Field(..., description="Payment status")
    total_amount: float = Field(..., description="Total amount")
    currency_code: str = Field(..., description="Currency code")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class PaymentCaptureRequest(BaseModel):
    """Request model for capturing/completing a payment."""

    paypal_order_id: str = Field(..., description="PayPal order ID to capture")
    payer_email: Optional[EmailStr] = Field(None, description="Payer's email address")


class PaymentSummary(BaseModel):
    """Summary model for payment history listings."""

    id: str = Field(..., description="Payment record ID")
    paypal_order_id: str = Field(..., description="PayPal order ID")
    status: str = Field(..., description="Payment status")
    total_amount: float = Field(..., description="Total amount")
    currency_code: str = Field(..., description="Currency code")
    item_count: int = Field(..., description="Number of items in the order")
    created_at: datetime = Field(..., description="Creation timestamp")
    payer_email: Optional[str] = Field(None, description="Payer's email")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
