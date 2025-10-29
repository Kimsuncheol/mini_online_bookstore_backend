"""
Coupon Service

Provides business logic and database operations for coupon management.
Handles coupon creation, usage, expiration, and tracking.
"""

from typing import List, Optional, Any, Dict
from datetime import datetime
from google.cloud.firestore import DocumentSnapshot
from app.models.coupon import (
    Coupon,
    CouponCreate,
    CouponUpdate,
    CouponSummary,
    CouponIssueRecord,
    CouponIssueRecordResponse,
)
from app.utils.firebase_config import get_firestore_client


class CouponService:
    """Service class for coupon-related database operations."""

    COUPON_COLLECTION = "coupons"
    COUPON_ISSUE_RECORDS_COLLECTION = "coupon_issue_records"

    def __init__(self):
        """Initialize the coupon service with Firestore client."""
        self.db: Any = get_firestore_client()

    # ==================== COUPON CRUD OPERATIONS ====================

    def create_coupon(
        self, user_id: str, user_email: str, coupon_data: CouponCreate
    ) -> Coupon:
        """
        Create a new coupon for a user.

        Args:
            user_id (str): User ID
            user_email (str): User's email
            coupon_data (CouponCreate): Coupon data

        Returns:
            Coupon: Created coupon

        Raises:
            Exception: If coupon data is invalid or database error occurs
        """
        try:
            if not coupon_data:
                raise ValueError("No coupon data provided")

            now = datetime.now()
            doc_ref = self.db.collection(self.COUPON_COLLECTION).document()

            coupon_dict = coupon_data.model_dump()
            coupon_dict.update({
                "user_id": user_id,
                "user_email": user_email,
                "used": False,
                "issued": False,
                "created_at": now,
                "updated_at": now,
            })

            doc_ref.set(coupon_dict)

            return Coupon(
                id=doc_ref.id,
                user_email=user_email,
                created_at=now,
                updated_at=now,
                **coupon_dict,
            )
        except ValueError as e:
            raise Exception(f"Invalid coupon data: {str(e)}")
        except Exception as e:
            raise Exception(f"Error creating coupon: {str(e)}")

    def get_coupon(self, coupon_id: str, user_email: str) -> Optional[Coupon]:
        """
        Get a coupon by ID.

        Args:
            coupon_id (str): Coupon ID
            user_email (str): User's email (for verification)

        Returns:
            Optional[Coupon]: Coupon if found, None otherwise
        """
        try:
            doc = self.db.collection(self.COUPON_COLLECTION).document(coupon_id).get()

            if not doc.exists:
                return None

            data = doc.to_dict()

            # Verify ownership
            if data.get("user_email") != user_email:
                return None

            return self._doc_to_coupon(doc)
        except Exception as e:
            raise Exception(f"Error fetching coupon: {str(e)}")

    def get_user_coupons(
        self, user_email: str, active_only: bool = False
    ) -> Dict[str, Any]:
        """
        Get all coupons for a user.

        Args:
            user_email (str): User's email
            active_only (bool): Return only active (unused and non-expired) coupons

        Returns:
            Dict: List of coupons and count
        """
        try:
            query = self.db.collection(self.COUPON_COLLECTION).where(
                "user_email", "==", user_email
            )

            if active_only:
                today = datetime.now().strftime("%Y-%m-%d")
                query = query.where("used", "==", False).where(
                    "expiration_date", ">=", today
                )

            docs = query.stream()

            coupons = []
            for doc in docs:
                coupon = self._doc_to_coupon(doc)
                coupons.append(coupon)

            return {
                "coupons": coupons,
                "count": len(coupons),
            }
        except Exception as e:
            raise Exception(f"Error fetching user coupons: {str(e)}")

    def update_coupon(
        self, coupon_id: str, user_email: str, update_data: CouponUpdate
    ) -> Coupon:
        """
        Update a coupon.

        Args:
            coupon_id (str): Coupon ID
            user_email (str): User's email
            update_data (CouponUpdate): Fields to update

        Returns:
            Coupon: Updated coupon

        Raises:
            Exception: If coupon not found or database error occurs
        """
        try:
            coupon_ref = self.db.collection(self.COUPON_COLLECTION).document(coupon_id)
            coupon_doc = coupon_ref.get()

            if not coupon_doc.exists:
                raise ValueError("Coupon not found")

            data = coupon_doc.to_dict()
            if data.get("user_email") != user_email:
                raise ValueError("Unauthorized access to coupon")

            if not update_data.model_dump(exclude_unset=True):
                raise ValueError("No update data provided")

            update_dict = update_data.model_dump(exclude_unset=True)
            update_dict["updated_at"] = datetime.now()

            coupon_ref.update(update_dict)

            updated_doc = coupon_ref.get()
            return self._doc_to_coupon(updated_doc)
        except ValueError as e:
            raise Exception(str(e))
        except Exception as e:
            raise Exception(f"Error updating coupon: {str(e)}")

    def delete_coupon(self, coupon_id: str, user_email: str) -> Dict[str, str]:
        """
        Delete a coupon.

        Args:
            coupon_id (str): Coupon ID
            user_email (str): User's email

        Returns:
            Dict: Confirmation message

        Raises:
            Exception: If database error occurs
        """
        try:
            coupon_ref = self.db.collection(self.COUPON_COLLECTION).document(coupon_id)
            coupon_doc = coupon_ref.get()

            if coupon_doc.exists:
                data = coupon_doc.to_dict()
                if data.get("user_email") == user_email:
                    coupon_ref.delete()

            return {"message": "Coupon deleted successfully"}
        except Exception as e:
            raise Exception(f"Error deleting coupon: {str(e)}")

    # ==================== COUPON USAGE OPERATIONS ====================

    def use_coupon(self, coupon_id: str, user_email: str) -> Coupon:
        """
        Mark a coupon as used.

        Args:
            coupon_id (str): Coupon ID
            user_email (str): User's email

        Returns:
            Coupon: Updated coupon with used status

        Raises:
            Exception: If coupon not found, already used, expired, or database error
        """
        try:
            coupon_ref = self.db.collection(self.COUPON_COLLECTION).document(coupon_id)
            coupon_doc = coupon_ref.get()

            if not coupon_doc.exists:
                raise ValueError("Coupon not found")

            data = coupon_doc.to_dict()

            if data.get("user_email") != user_email:
                raise ValueError("Unauthorized access to coupon")

            if data.get("used"):
                raise ValueError("Coupon already used")

            # Check expiration
            expiration_date = data.get("expiration_date")
            if expiration_date:
                today = datetime.now().strftime("%Y-%m-%d")
                if expiration_date < today:
                    raise ValueError("Coupon expired")

            # Mark as used
            now = datetime.now()
            today = datetime.now().strftime("%Y-%m-%d")
            coupon_ref.update({
                "used": True,
                "used_date": today,
                "updated_at": now,
            })

            updated_doc = coupon_ref.get()
            return self._doc_to_coupon(updated_doc)
        except ValueError as e:
            raise Exception(str(e))
        except Exception as e:
            raise Exception(f"Error using coupon: {str(e)}")

    def issue_coupon(
        self, coupon_id: str, user_id: str, user_email: str
    ) -> Coupon:
        """
        Mark a coupon as issued.

        Args:
            coupon_id (str): Coupon ID
            user_id (str): User ID
            user_email (str): User's email

        Returns:
            Coupon: Updated coupon with issued status

        Raises:
            Exception: If coupon not found or database error occurs
        """
        try:
            coupon_ref = self.db.collection(self.COUPON_COLLECTION).document(coupon_id)
            coupon_doc = coupon_ref.get()

            if not coupon_doc.exists:
                raise ValueError("Coupon not found")

            now = datetime.now()
            today = datetime.now().strftime("%Y-%m-%d")

            coupon_ref.update({
                "issued": True,
                "issued_date": today,
                "updated_at": now,
            })

            updated_doc = coupon_ref.get()
            return self._doc_to_coupon(updated_doc)
        except ValueError as e:
            raise Exception(str(e))
        except Exception as e:
            raise Exception(f"Error issuing coupon: {str(e)}")

    # ==================== COUPON ISSUE RECORD OPERATIONS ====================

    def create_coupon_issue_record(
        self,
        user_id: str,
        user_email: str,
        streak_days: int,
        coupon_value: float,
    ) -> CouponIssueRecordResponse:
        """
        Create a coupon issue record for a streak milestone.

        Args:
            user_id (str): User ID
            user_email (str): User's email
            streak_days (int): Streak days (7, 14, 30, etc)
            coupon_value (float): Coupon value in dollars

        Returns:
            CouponIssueRecordResponse: Created issue record

        Raises:
            Exception: If database error or coupon already issued for this milestone
        """
        try:
            # Check if already issued for this milestone
            existing = (
                self.db.collection(self.COUPON_ISSUE_RECORDS_COLLECTION)
                .where("user_email", "==", user_email)
                .where("streak_days", "==", streak_days)
                .stream()
            )

            if list(existing):
                raise ValueError(
                    f"Coupon already issued for {streak_days} day streak"
                )

            # Create issue record
            now = datetime.now()
            doc_ref = self.db.collection(self.COUPON_ISSUE_RECORDS_COLLECTION).document()

            issue_record = {
                "user_id": user_id,
                "user_email": user_email,
                "streak_days": streak_days,
                "coupon_value": coupon_value,
                "coupon_id": None,
                "issued": False,
                "issued_at": None,
                "created_at": now,
            }

            doc_ref.set(issue_record)

            return CouponIssueRecordResponse(
                id=doc_ref.id,
                user_id=user_id,
                user_email=user_email,
                streak_days=streak_days,
                coupon_value=coupon_value,
                coupon_id=None,
                issued=False,
                issued_at=None,
                created_at=now,
            )
        except ValueError as e:
            raise Exception(str(e))
        except Exception as e:
            raise Exception(f"Error creating coupon issue record: {str(e)}")

    def get_coupon_issue_records(
        self, user_email: str
    ) -> List[CouponIssueRecordResponse]:
        """
        Get all coupon issue records for a user.

        Args:
            user_email (str): User's email

        Returns:
            List[CouponIssueRecordResponse]: List of coupon issue records
        """
        try:
            docs = (
                self.db.collection(self.COUPON_ISSUE_RECORDS_COLLECTION)
                .where("user_email", "==", user_email)
                .order_by("created_at", direction=2)  # Descending
                .stream()
            )

            records = []
            for doc in docs:
                data = doc.to_dict()
                records.append(
                    CouponIssueRecordResponse(
                        id=doc.id,
                        user_id=data.get("user_id"),
                        user_email=data.get("user_email"),
                        streak_days=data.get("streak_days"),
                        coupon_value=data.get("coupon_value"),
                        coupon_id=data.get("coupon_id"),
                        issued=data.get("issued", False),
                        issued_at=data.get("issued_at"),
                        created_at=data.get("created_at"),
                    )
                )

            return records
        except Exception as e:
            raise Exception(f"Error fetching coupon issue records: {str(e)}")

    # ==================== HELPER METHODS ====================

    def _doc_to_coupon(self, doc: DocumentSnapshot) -> Coupon:
        """
        Convert a Firestore document to a Coupon object.

        Args:
            doc (DocumentSnapshot): Firestore document

        Returns:
            Coupon: Coupon object
        """
        data = doc.to_dict()
        return Coupon(
            id=doc.id,
            code=data.get("code"),
            user_email=data.get("user_email"),
            discount_value=data.get("discount_value"),
            source=data.get("source", "manual"),
            description=data.get("description"),
            used=data.get("used", False),
            used_date=data.get("used_date"),
            issued=data.get("issued", False),
            issued_date=data.get("issued_date"),
            expiration_date=data.get("expiration_date"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


def get_coupon_service() -> CouponService:
    """Factory function to get CouponService instance."""
    return CouponService()


__all__ = ["CouponService", "get_coupon_service"]
