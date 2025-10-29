"""
Check-In Service

Provides business logic and database operations for user check-in functionality.
Handles streak tracking, check-in records, and coupon earning.
"""

from typing import List, Optional, Any, Dict
from datetime import datetime, timedelta
from google.cloud.firestore import DocumentSnapshot
from app.models.check_in import (
    CheckIn,
    CheckInCreate,
    CheckInUpdate,
    CheckInStats,
    CheckInRecord,
    CheckInProfile,
)
from app.utils.firebase_config import get_firestore_client


class CheckInService:
    """Service class for check-in-related database operations."""

    CHECK_IN_COLLECTION = "check_ins"
    CHECK_IN_RECORDS_COLLECTION = "check_in_records"

    def __init__(self):
        """Initialize the check-in service with Firestore client."""
        self.db: Any = get_firestore_client()

    # ==================== CHECK-IN CRUD OPERATIONS ====================

    def create_or_update_check_in(
        self, user_id: str, user_email: str, user_name: str
    ) -> Dict[str, Any]:
        """
        Create or update a check-in record for a user.

        Args:
            user_id (str): User ID
            user_email (str): User's email
            user_name (str): User's display name

        Returns:
            Dict: Check-in response with updated statistics and earned coupons
        """
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            check_in_ref = self.db.collection(self.CHECK_IN_COLLECTION).document(
                user_email
            )
            check_in_doc = check_in_ref.get()

            now = datetime.now()
            earned_coupons = []

            if check_in_doc.exists:
                # User has existing check-in record
                data = check_in_doc.to_dict()
                last_check_in_date = data.get("last_check_in_date")

                if last_check_in_date == today:
                    # Already checked in today
                    return {
                        "success": False,
                        "message": "Already checked in today",
                        "stats": CheckInStats(
                            current_streak=data.get("current_streak", 0),
                            longest_streak=data.get("longest_streak", 0),
                            total_check_ins=data.get("total_check_ins", 0),
                            last_check_in_date=last_check_in_date,
                        ),
                        "earned_coupons": [],
                        "checked_in_today": True,
                    }

                # Calculate streak
                current_streak = data.get("current_streak", 0)
                longest_streak = data.get("longest_streak", 0)
                total_check_ins = data.get("total_check_ins", 0)

                if last_check_in_date:
                    last_date = datetime.strptime(last_check_in_date, "%Y-%m-%d")
                    today_date = datetime.strptime(today, "%Y-%m-%d")
                    days_diff = (today_date - last_date).days

                    if days_diff == 1:
                        # Streak continues
                        current_streak += 1
                    else:
                        # Streak broken, reset to 1
                        current_streak = 1
                else:
                    current_streak = 1

                # Update longest streak
                if current_streak > longest_streak:
                    longest_streak = current_streak

                total_check_ins += 1

                # Check for coupon milestones (7, 14, 30 days)
                milestone_days = [7, 14, 30]
                for milestone in milestone_days:
                    if current_streak == milestone:
                        coupon_data = {
                            "earned_on_streak": milestone,
                            "value": self._get_coupon_value_for_streak(milestone),
                        }
                        earned_coupons.append(coupon_data)

            else:
                # First check-in for this user
                current_streak = 1
                longest_streak = 1
                total_check_ins = 1

            # Record the daily check-in
            self._record_daily_check_in(user_email, today)

            # Update check-in document
            update_data = {
                "user_id": user_id,
                "user_name": user_name,
                "current_streak": current_streak,
                "longest_streak": longest_streak,
                "total_check_ins": total_check_ins,
                "last_check_in_date": today,
                "checked_in_today": True,
                "updated_at": now,
            }

            if not check_in_doc.exists:
                update_data["created_at"] = now

            check_in_ref.set(update_data, merge=True)

            return {
                "success": True,
                "message": "Check-in successful",
                "stats": CheckInStats(
                    current_streak=current_streak,
                    longest_streak=longest_streak,
                    total_check_ins=total_check_ins,
                    last_check_in_date=today,
                ),
                "earned_coupons": earned_coupons,
                "checked_in_today": True,
            }

        except Exception as e:
            raise Exception(f"Error creating/updating check-in: {str(e)}")

    def get_check_in_stats(self, user_email: str) -> Optional[CheckInStats]:
        """
        Get check-in statistics for a user.

        Args:
            user_email (str): User's email address

        Returns:
            Optional[CheckInStats]: User's check-in statistics or None
        """
        try:
            check_in_ref = self.db.collection(self.CHECK_IN_COLLECTION).document(
                user_email
            )
            doc = check_in_ref.get()

            if not doc.exists:
                return None

            data = doc.to_dict()
            return CheckInStats(
                current_streak=data.get("current_streak", 0),
                longest_streak=data.get("longest_streak", 0),
                total_check_ins=data.get("total_check_ins", 0),
                last_check_in_date=data.get("last_check_in_date"),
            )
        except Exception as e:
            raise Exception(f"Error fetching check-in stats: {str(e)}")

    def get_user_check_in_profile(
        self, user_id: str, user_email: str, user_name: str
    ) -> Optional[CheckInProfile]:
        """
        Get complete check-in profile for a user.

        Args:
            user_id (str): User ID
            user_email (str): User's email
            user_name (str): User's display name

        Returns:
            Optional[CheckInProfile]: User's complete check-in profile
        """
        try:
            check_in_ref = self.db.collection(self.CHECK_IN_COLLECTION).document(
                user_email
            )
            doc = check_in_ref.get()

            if not doc.exists:
                return None

            data = doc.to_dict()

            # Get recent check-in records
            recent_records = self.get_check_in_records(user_email, days=30)

            # Get earned coupons (from coupon service)
            coupons = []  # This would be populated from coupon service

            return CheckInProfile(
                user_id=user_id,
                user_email=user_email,
                user_name=user_name,
                stats=CheckInStats(
                    current_streak=data.get("current_streak", 0),
                    longest_streak=data.get("longest_streak", 0),
                    total_check_ins=data.get("total_check_ins", 0),
                    last_check_in_date=data.get("last_check_in_date"),
                ),
                recent_records=recent_records,
                coupons=coupons,
                created_at=data.get("created_at", datetime.now()),
                updated_at=data.get("updated_at", datetime.now()),
            )
        except Exception as e:
            raise Exception(f"Error fetching check-in profile: {str(e)}")

    def get_check_in_records(
        self, user_email: str, days: int = 90
    ) -> List[CheckInRecord]:
        """
        Get check-in records for a user.

        Args:
            user_email (str): User's email address
            days (int): Number of days to retrieve (max 365)

        Returns:
            List[CheckInRecord]: List of check-in records
        """
        try:
            max_days = min(days, 365)
            records_collection = (
                self.db.collection(self.CHECK_IN_COLLECTION)
                .document(user_email)
                .collection(self.CHECK_IN_RECORDS_COLLECTION)
            )

            # Query last N days
            start_date = (datetime.now() - timedelta(days=max_days)).strftime(
                "%Y-%m-%d"
            )

            docs = (
                records_collection.where("date", ">=", start_date)
                .order_by("date", direction=2)  # Descending
                .stream()
            )

            records = []
            for doc in docs:
                data = doc.to_dict()
                records.append(
                    CheckInRecord(
                        date=data.get("date"),
                        checked_in=data.get("checked_in", True),
                    )
                )

            return records
        except Exception as e:
            raise Exception(f"Error fetching check-in records: {str(e)}")

    def reset_daily_flags(self) -> Dict[str, Any]:
        """
        Reset checked_in_today flag for all users.

        Called once per day via scheduled task/cron job.

        Returns:
            Dict: Confirmation message with updated user count
        """
        try:
            check_in_docs = self.db.collection(self.CHECK_IN_COLLECTION).stream()

            updated_count = 0
            for doc in check_in_docs:
                doc.reference.update({"checked_in_today": False})
                updated_count += 1

            return {
                "success": True,
                "message": f"Reset check-in flags for {updated_count} users",
                "updated_count": updated_count,
            }
        except Exception as e:
            raise Exception(f"Error resetting daily flags: {str(e)}")

    # ==================== HELPER METHODS ====================

    def _record_daily_check_in(self, user_email: str, date: str) -> None:
        """
        Record a daily check-in in the user's check-in records subcollection.

        Args:
            user_email (str): User's email
            date (str): Date in YYYY-MM-DD format
        """
        try:
            records_ref = (
                self.db.collection(self.CHECK_IN_COLLECTION)
                .document(user_email)
                .collection(self.CHECK_IN_RECORDS_COLLECTION)
                .document(date)
            )

            records_ref.set({
                "date": date,
                "checked_in": True,
                "timestamp": datetime.now(),
            })
        except Exception as e:
            raise Exception(f"Error recording daily check-in: {str(e)}")

    def _get_coupon_value_for_streak(self, streak_days: int) -> float:
        """
        Get coupon value based on streak milestone.

        Args:
            streak_days (int): Number of consecutive days

        Returns:
            float: Coupon value in dollars
        """
        coupon_values = {
            7: 2.0,
            14: 4.0,
            30: 10.0,
        }
        return coupon_values.get(streak_days, 1.0)


def get_check_in_service() -> CheckInService:
    """Factory function to get CheckInService instance."""
    return CheckInService()


__all__ = ["CheckInService", "get_check_in_service"]
