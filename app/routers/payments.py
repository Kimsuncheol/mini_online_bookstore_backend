"""
Payments Router

Handles payment-related operations including:
- Creating payment records
- Updating payment status (capture, cancel)
- Retrieving payment history
- Payment statistics
"""

from fastapi import APIRouter, HTTPException, Path, Query
from typing import Optional
from app.models.payment import (
    PaymentHistory,
    PaymentHistoryCreate,
    PaymentHistoryUpdate,
    PaymentCaptureRequest,
    PaymentOrderResponse,
    PaymentSummary,
)
from app.services.payment_service import get_payment_service

router = APIRouter(prefix="/api/payments", tags=["payments"])


# ==================== PAYMENT CRUD ENDPOINTS ====================


@router.post("", status_code=201)
async def create_payment_record(payment_data: PaymentHistoryCreate):
    """
    Create a new payment record in the payment history.

    This endpoint should be called after a PayPal order is created
    to store the order information in the database.

    Args:
        payment_data (PaymentHistoryCreate): The payment data to create

    Returns:
        PaymentOrderResponse: The created payment record information

    Raises:
        HTTPException: 400 if invalid data, 500 if database error occurs
    """
    try:
        payment_service = get_payment_service()
        payment = payment_service.create_payment_record(payment_data)

        return PaymentOrderResponse(
            id=payment.id,
            paypal_order_id=payment.paypal_order_id,
            status=payment.status,
            total_amount=payment.total_amount,
            currency_code=payment.currency_code,
            created_at=payment.created_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating payment record: {str(e)}")


@router.get("/{payment_id}")
async def get_payment(payment_id: str = Path(..., description="The payment record ID")):
    """
    Fetch a payment record by its ID.

    Args:
        payment_id (str): The unique identifier of the payment record

    Returns:
        PaymentHistory: The payment record data

    Raises:
        HTTPException: 404 if payment not found, 500 if database error occurs
    """
    try:
        payment_service = get_payment_service()
        payment = payment_service.get_payment_by_id(payment_id)

        if payment is None:
            raise HTTPException(
                status_code=404, detail=f"Payment record with ID '{payment_id}' not found"
            )

        return payment.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching payment: {str(e)}")


@router.get("/paypal/{paypal_order_id}")
async def get_payment_by_paypal_order_id(
    paypal_order_id: str = Path(..., description="The PayPal order ID")
):
    """
    Fetch a payment record by PayPal order ID.

    Args:
        paypal_order_id (str): The PayPal order ID

    Returns:
        PaymentHistory: The payment record data

    Raises:
        HTTPException: 404 if payment not found, 500 if database error occurs
    """
    try:
        payment_service = get_payment_service()
        payment = payment_service.get_payment_by_paypal_order_id(paypal_order_id)

        if payment is None:
            raise HTTPException(
                status_code=404,
                detail=f"Payment record with PayPal order ID '{paypal_order_id}' not found",
            )

        return payment.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching payment: {str(e)}")


@router.get("")
async def get_all_payments(
    limit: Optional[int] = Query(None, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by payment status"),
):
    """
    Fetch all payment records.

    Admin endpoint to retrieve all payments with optional filtering.

    Args:
        limit (Optional[int]): Maximum number of records to return
        status (Optional[str]): Filter by payment status (created, approved, completed, failed, cancelled)

    Returns:
        list: List of payment summaries

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        payment_service = get_payment_service()
        payments = payment_service.get_all_payments(limit=limit, status=status)
        return [payment_service.payment_to_summary(p).model_dump() for p in payments]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching payments: {str(e)}")


# ==================== USER-SPECIFIC ENDPOINTS ====================


@router.get("/user/{user_id}")
async def get_user_payments(
    user_id: str = Path(..., description="The user ID"),
    limit: Optional[int] = Query(None, ge=1, le=100),
):
    """
    Fetch payment records for a specific user.

    Args:
        user_id (str): The user ID
        limit (Optional[int]): Maximum number of records to return

    Returns:
        list: List of payment summaries for the user

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        payment_service = get_payment_service()
        payments = payment_service.get_payments_by_user(user_id, limit=limit)
        return [payment_service.payment_to_summary(p).model_dump() for p in payments]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching payments for user: {str(e)}"
        )


@router.get("/email/{email}")
async def get_email_payments(
    email: str = Path(..., description="The payer email address"),
    limit: Optional[int] = Query(None, ge=1, le=100),
):
    """
    Fetch payment records for a specific payer email.

    Args:
        email (str): The payer's email address
        limit (Optional[int]): Maximum number of records to return

    Returns:
        list: List of payment summaries for the email

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        payment_service = get_payment_service()
        payments = payment_service.get_payments_by_email(email, limit=limit)
        return [payment_service.payment_to_summary(p).model_dump() for p in payments]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching payments for email: {str(e)}"
        )


# ==================== PAYMENT STATUS UPDATE ENDPOINTS ====================


@router.patch("/{payment_id}")
async def update_payment(
    payment_id: str = Path(..., description="The payment record ID"),
    update_data: PaymentHistoryUpdate = None,
):
    """
    Update an existing payment record.

    Args:
        payment_id (str): The ID of the payment record to update
        update_data (PaymentHistoryUpdate): The data to update

    Returns:
        PaymentHistory: The updated payment record

    Raises:
        HTTPException: 400 if invalid data, 404 if not found, 500 if database error occurs
    """
    try:
        if not update_data:
            raise HTTPException(status_code=400, detail="Update data is required")

        payment_service = get_payment_service()
        updated_payment = payment_service.update_payment(payment_id, update_data)

        if updated_payment is None:
            raise HTTPException(
                status_code=404, detail=f"Payment record with ID '{payment_id}' not found"
            )

        return updated_payment.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating payment: {str(e)}")


@router.post("/capture")
async def capture_payment(capture_request: PaymentCaptureRequest):
    """
    Mark a payment as completed (captured).

    This endpoint should be called after a PayPal order is successfully captured
    to update the payment status in the database.

    Args:
        capture_request (PaymentCaptureRequest): Capture request with PayPal order ID

    Returns:
        PaymentHistory: The updated payment record

    Raises:
        HTTPException: 404 if payment not found, 500 if database error occurs
    """
    try:
        payment_service = get_payment_service()
        updated_payment = payment_service.capture_payment(
            capture_request.paypal_order_id, capture_request.payer_email
        )

        if updated_payment is None:
            raise HTTPException(
                status_code=404,
                detail=f"Payment with PayPal order ID '{capture_request.paypal_order_id}' not found",
            )

        return updated_payment.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error capturing payment: {str(e)}")


@router.post("/cancel/{paypal_order_id}")
async def cancel_payment(paypal_order_id: str = Path(..., description="The PayPal order ID")):
    """
    Mark a payment as cancelled.

    This endpoint should be called when a user cancels a PayPal order
    to update the payment status in the database.

    Args:
        paypal_order_id (str): The PayPal order ID

    Returns:
        PaymentHistory: The updated payment record

    Raises:
        HTTPException: 404 if payment not found, 500 if database error occurs
    """
    try:
        payment_service = get_payment_service()
        updated_payment = payment_service.cancel_payment(paypal_order_id)

        if updated_payment is None:
            raise HTTPException(
                status_code=404,
                detail=f"Payment with PayPal order ID '{paypal_order_id}' not found",
            )

        return updated_payment.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling payment: {str(e)}")


# ==================== STATISTICS ENDPOINTS ====================


@router.get("/statistics/all")
async def get_payment_statistics():
    """
    Get overall payment statistics.

    Returns statistics for all payments including total counts,
    revenue breakdown by currency, and payment status distribution.

    Returns:
        dict: Payment statistics

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        payment_service = get_payment_service()
        statistics = payment_service.get_payment_statistics()
        return statistics
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error calculating payment statistics: {str(e)}"
        )


@router.get("/statistics/user/{user_id}")
async def get_user_payment_statistics(user_id: str = Path(..., description="The user ID")):
    """
    Get payment statistics for a specific user.

    Returns statistics for a user's payments including total counts,
    revenue breakdown by currency, and payment status distribution.

    Args:
        user_id (str): The user ID

    Returns:
        dict: Payment statistics for the user

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        payment_service = get_payment_service()
        statistics = payment_service.get_payment_statistics(user_id=user_id)
        return statistics
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error calculating payment statistics: {str(e)}"
        )
