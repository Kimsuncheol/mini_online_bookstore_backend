"""
Payment Service

Provides business logic and database operations for managing payment history.
Includes CRUD operations for payment records and PayPal order tracking.
"""

from typing import List, Optional, Any, Dict
from datetime import datetime
from google.cloud.firestore import DocumentSnapshot
from app.models.payment import (
    PaymentHistory,
    PaymentHistoryCreate,
    PaymentHistoryUpdate,
    PaymentItem,
    PaymentOrderResponse,
    PaymentSummary,
)
from app.utils.firebase_config import get_firestore_client


class PaymentService:
    """Service class for payment-related database operations."""

    PAYMENT_HISTORY_COLLECTION = "payment_history"

    def __init__(self):
        """Initialize the payment service with Firestore client."""
        self.db: Any = get_firestore_client()

    # ==================== PAYMENT CRUD OPERATIONS ====================

    def create_payment_record(self, payment_data: PaymentHistoryCreate) -> PaymentHistory:
        """
        Create a new payment record in the payment history.

        Args:
            payment_data (PaymentHistoryCreate): The payment data to create

        Returns:
            PaymentHistory: The created payment record with ID

        Raises:
            Exception: If there's an error creating the payment record
        """
        try:
            now = datetime.now()

            # Convert items to dictionaries
            items_dict = [item.model_dump() for item in payment_data.items]

            data = {
                **payment_data.model_dump(exclude={"items"}),
                "items": items_dict,
                "created_at": now,
                "updated_at": now,
            }

            doc_ref = self.db.collection(self.PAYMENT_HISTORY_COLLECTION).document()
            doc_ref.set(data)

            return PaymentHistory(
                id=doc_ref.id,
                created_at=now,
                updated_at=now,
                **payment_data.model_dump(),
            )
        except Exception as e:
            raise Exception(f"Error creating payment record: {str(e)}")

    def get_payment_by_id(self, payment_id: str) -> Optional[PaymentHistory]:
        """
        Fetch a payment record by its ID.

        Args:
            payment_id (str): The unique identifier of the payment record

        Returns:
            Optional[PaymentHistory]: Payment record if found, None otherwise

        Raises:
            Exception: If there's an error fetching the payment record
        """
        try:
            doc = self.db.collection(self.PAYMENT_HISTORY_COLLECTION).document(payment_id).get()

            if doc.exists:
                return self._document_to_payment(doc)
            else:
                return None
        except Exception as e:
            raise Exception(f"Error fetching payment with ID {payment_id}: {str(e)}")

    def get_payment_by_paypal_order_id(self, paypal_order_id: str) -> Optional[PaymentHistory]:
        """
        Fetch a payment record by PayPal order ID.

        Args:
            paypal_order_id (str): The PayPal order ID

        Returns:
            Optional[PaymentHistory]: Payment record if found, None otherwise

        Raises:
            Exception: If there's an error fetching the payment record
        """
        try:
            docs = (
                self.db.collection(self.PAYMENT_HISTORY_COLLECTION)
                .where("paypal_order_id", "==", paypal_order_id)
                .limit(1)
                .stream()
            )

            for doc in docs:
                return self._document_to_payment(doc)

            return None
        except Exception as e:
            raise Exception(
                f"Error fetching payment with PayPal order ID {paypal_order_id}: {str(e)}"
            )

    def get_all_payments(
        self, limit: Optional[int] = None, status: Optional[str] = None
    ) -> List[PaymentHistory]:
        """
        Fetch all payment records.

        Args:
            limit (Optional[int]): Maximum number of records to return
            status (Optional[str]): Filter by payment status

        Returns:
            List[PaymentHistory]: List of payment records

        Raises:
            Exception: If there's an error fetching payment records
        """
        try:
            query = self.db.collection(self.PAYMENT_HISTORY_COLLECTION).order_by(
                "created_at", direction="DESCENDING"
            )

            if status:
                query = query.where("status", "==", status)

            if limit:
                query = query.limit(limit)

            docs = query.stream()
            payments = [self._document_to_payment(doc) for doc in docs]
            return payments
        except Exception as e:
            raise Exception(f"Error fetching all payments: {str(e)}")

    def get_payments_by_user(
        self, user_id: str, limit: Optional[int] = None
    ) -> List[PaymentHistory]:
        """
        Fetch payment records for a specific user.

        Args:
            user_id (str): The user ID
            limit (Optional[int]): Maximum number of records to return

        Returns:
            List[PaymentHistory]: List of payment records for the user

        Raises:
            Exception: If there's an error fetching payment records
        """
        try:
            query = (
                self.db.collection(self.PAYMENT_HISTORY_COLLECTION)
                .where("user_id", "==", user_id)
                .order_by("created_at", direction="DESCENDING")
            )

            if limit:
                query = query.limit(limit)

            docs = query.stream()
            payments = [self._document_to_payment(doc) for doc in docs]
            return payments
        except Exception as e:
            raise Exception(f"Error fetching payments for user {user_id}: {str(e)}")

    def get_payments_by_email(
        self, payer_email: str, limit: Optional[int] = None
    ) -> List[PaymentHistory]:
        """
        Fetch payment records for a specific payer email.

        Args:
            payer_email (str): The payer's email address
            limit (Optional[int]): Maximum number of records to return

        Returns:
            List[PaymentHistory]: List of payment records for the email

        Raises:
            Exception: If there's an error fetching payment records
        """
        try:
            query = (
                self.db.collection(self.PAYMENT_HISTORY_COLLECTION)
                .where("payer_email", "==", payer_email)
                .order_by("created_at", direction="DESCENDING")
            )

            if limit:
                query = query.limit(limit)

            docs = query.stream()
            payments = [self._document_to_payment(doc) for doc in docs]
            return payments
        except Exception as e:
            raise Exception(f"Error fetching payments for email {payer_email}: {str(e)}")

    def search_payments(
        self,
        *,
        payer_email: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        book_name: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[PaymentHistory]:
        """
        Search payment history using optional filters.

        Args:
            payer_email: Filter by payer email
            start_date: Inclusive start timestamp
            end_date: Inclusive end timestamp
            min_amount: Minimum total order amount
            max_amount: Maximum total order amount
            book_name: Case-insensitive match against purchased book titles
            limit: Maximum number of records to return

        Returns:
            List[PaymentHistory]: Filtered payment records ordered by newest first
        """
        try:
            collection = self.db.collection(self.PAYMENT_HISTORY_COLLECTION)
            query = collection

            if payer_email:
                query = query.where("payer_email", "==", payer_email)

            if start_date:
                query = query.where("created_at", ">=", start_date)

            if end_date:
                query = query.where("created_at", "<=", end_date)

            query = query.order_by("created_at", direction="DESCENDING")

            book_name_filter = (book_name or "").strip().lower()
            needs_post_filter = (
                bool(book_name_filter) or min_amount is not None or max_amount is not None
            )

            if limit and not needs_post_filter:
                query = query.limit(limit)

            docs = query.stream()
            payments = [self._document_to_payment(doc) for doc in docs]

            filtered: List[PaymentHistory] = []
            for payment in payments:
                if min_amount is not None and payment.total_amount < min_amount:
                    continue
                if max_amount is not None and payment.total_amount > max_amount:
                    continue

                if book_name_filter:
                    matches_book = any(
                        book_name_filter in (item.book_title or "").lower()
                        for item in payment.items
                    )
                    if not matches_book:
                        continue

                filtered.append(payment)

            if limit:
                return filtered[:limit]

            return filtered
        except Exception as e:
            raise Exception(f"Error searching payment history: {str(e)}")

    def update_payment(
        self, payment_id: str, update_data: PaymentHistoryUpdate
    ) -> Optional[PaymentHistory]:
        """
        Update an existing payment record.

        Args:
            payment_id (str): The ID of the payment record to update
            update_data (PaymentHistoryUpdate): The data to update

        Returns:
            Optional[PaymentHistory]: Updated payment record, or None if not found

        Raises:
            Exception: If there's an error updating the payment record
        """
        try:
            doc_ref = self.db.collection(self.PAYMENT_HISTORY_COLLECTION).document(payment_id)

            # Check if document exists
            if not doc_ref.get().exists:
                return None

            update_fields = {
                k: v for k, v in update_data.model_dump().items() if v is not None
            }
            update_fields["updated_at"] = datetime.now()

            doc_ref.update(update_fields)

            # Fetch and return the updated payment record
            return self.get_payment_by_id(payment_id)
        except Exception as e:
            raise Exception(f"Error updating payment with ID {payment_id}: {str(e)}")

    def update_payment_by_paypal_order_id(
        self, paypal_order_id: str, update_data: PaymentHistoryUpdate
    ) -> Optional[PaymentHistory]:
        """
        Update a payment record by PayPal order ID.

        Args:
            paypal_order_id (str): The PayPal order ID
            update_data (PaymentHistoryUpdate): The data to update

        Returns:
            Optional[PaymentHistory]: Updated payment record, or None if not found

        Raises:
            Exception: If there's an error updating the payment record
        """
        try:
            payment = self.get_payment_by_paypal_order_id(paypal_order_id)
            if not payment:
                return None

            return self.update_payment(payment.id, update_data)
        except Exception as e:
            raise Exception(
                f"Error updating payment with PayPal order ID {paypal_order_id}: {str(e)}"
            )

    def capture_payment(
        self, paypal_order_id: str, payer_email: Optional[str] = None
    ) -> Optional[PaymentHistory]:
        """
        Mark a payment as completed (captured).

        Args:
            paypal_order_id (str): The PayPal order ID
            payer_email (Optional[str]): The payer's email address

        Returns:
            Optional[PaymentHistory]: Updated payment record, or None if not found

        Raises:
            Exception: If there's an error capturing the payment
        """
        try:
            update_data = PaymentHistoryUpdate(status="completed", payer_email=payer_email)
            return self.update_payment_by_paypal_order_id(paypal_order_id, update_data)
        except Exception as e:
            raise Exception(f"Error capturing payment {paypal_order_id}: {str(e)}")

    def cancel_payment(self, paypal_order_id: str) -> Optional[PaymentHistory]:
        """
        Mark a payment as cancelled.

        Args:
            paypal_order_id (str): The PayPal order ID

        Returns:
            Optional[PaymentHistory]: Updated payment record, or None if not found

        Raises:
            Exception: If there's an error cancelling the payment
        """
        try:
            update_data = PaymentHistoryUpdate(status="cancelled")
            return self.update_payment_by_paypal_order_id(paypal_order_id, update_data)
        except Exception as e:
            raise Exception(f"Error cancelling payment {paypal_order_id}: {str(e)}")

    # ==================== STATISTICS AND ANALYTICS ====================

    def get_payment_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get payment statistics.

        Args:
            user_id (Optional[str]): Filter by user ID (if None, returns all)

        Returns:
            Dict containing:
                - total_payments: Total number of payments
                - completed_payments: Number of completed payments
                - total_revenue: Total revenue from completed payments
                - currency_breakdown: Revenue breakdown by currency

        Raises:
            Exception: If there's an error calculating statistics
        """
        try:
            if user_id:
                payments = self.get_payments_by_user(user_id)
            else:
                payments = self.get_all_payments()

            completed_payments = [p for p in payments if p.status == "completed"]

            # Calculate revenue by currency
            currency_breakdown = {}
            for payment in completed_payments:
                currency = payment.currency_code
                if currency not in currency_breakdown:
                    currency_breakdown[currency] = 0.0
                currency_breakdown[currency] += payment.total_amount

            return {
                "total_payments": len(payments),
                "completed_payments": len(completed_payments),
                "pending_payments": len([p for p in payments if p.status in ["created", "approved"]]),
                "failed_payments": len([p for p in payments if p.status == "failed"]),
                "cancelled_payments": len([p for p in payments if p.status == "cancelled"]),
                "currency_breakdown": currency_breakdown,
            }
        except Exception as e:
            raise Exception(f"Error calculating payment statistics: {str(e)}")

    # ==================== HELPER METHODS ====================

    @staticmethod
    def _document_to_payment(doc: DocumentSnapshot) -> PaymentHistory:
        """Convert a Firestore document snapshot to a PaymentHistory object."""
        data = doc.to_dict()

        # Convert items dictionaries back to PaymentItem objects
        items = [PaymentItem(**item) for item in data.get("items", [])]

        return PaymentHistory(
            id=doc.id,
            paypal_order_id=data.get("paypal_order_id"),
            status=data.get("status"),
            user_id=data.get("user_id"),
            payer_email=data.get("payer_email"),
            items=items,
            currency_code=data.get("currency_code", "USD"),
            total_amount=data.get("total_amount"),
            reference_id=data.get("reference_id"),
            notes=data.get("notes"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    @staticmethod
    def payment_to_summary(payment: PaymentHistory) -> PaymentSummary:
        """Convert a PaymentHistory object to a PaymentSummary."""
        return PaymentSummary(
            id=payment.id,
            paypal_order_id=payment.paypal_order_id,
            status=payment.status,
            total_amount=payment.total_amount,
            currency_code=payment.currency_code,
            item_count=len(payment.items),
            created_at=payment.created_at,
            payer_email=payment.payer_email,
        )


# Convenience function to create a service instance
def get_payment_service() -> PaymentService:
    """Create and return a payment service instance."""
    return PaymentService()
