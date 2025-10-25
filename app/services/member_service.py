"""
Member Service

Provides business logic and database operations for managing members.
"""

from typing import List, Optional, Any
from datetime import datetime
from google.cloud import firestore
from google.cloud.firestore import DocumentReference, DocumentSnapshot
from app.models.member import Member, MemberCreate, MemberUpdate
from app.utils.firebase_config import get_firestore_client


class MemberService:
    """Service class for member-related database operations."""

    COLLECTION_NAME = "members"

    def __init__(self):
        """Initialize the member service with Firestore client."""
        self.db: Any = get_firestore_client()

    def fetch_user_by_id(self, member_id: str) -> Optional[Member]:
        """
        Fetch a user from the members collection by member ID.

        Args:
            member_id (str): The unique identifier of the member document in Firestore

        Returns:
            Optional[Member]: Member object if found, None otherwise

        Raises:
            Exception: If there's an error accessing the database
        """
        try:
            doc = self.db.collection(self.COLLECTION_NAME).document(member_id).get()

            if doc.exists:
                return self._document_to_member(doc)
            else:
                return None
        except Exception as e:
            raise Exception(f"Error fetching member with ID {member_id}: {str(e)}")

    def fetch_user_by_email(self, email: str) -> Optional[Member]:
        """
        Fetch a user from the members collection by email address.

        Args:
            email (str): The email address of the member

        Returns:
            Optional[Member]: Member object if found, None otherwise

        Raises:
            Exception: If there's an error accessing the database
        """
        try:
            docs = (
                self.db.collection(self.COLLECTION_NAME)
                .where("email", "==", email)
                .limit(1)
                .stream()
            )

            for doc in docs:
                return self._document_to_member(doc)
            return None
        except Exception as e:
            raise Exception(f"Error fetching member with email {email}: {str(e)}")

    def fetch_all_users(self) -> List[Member]:
        """
        Fetch all users from the members collection.

        Returns:
            List[Member]: List of all member objects

        Raises:
            Exception: If there's an error accessing the database
        """
        try:
            docs = self.db.collection(self.COLLECTION_NAME).stream()
            members = [self._document_to_member(doc) for doc in docs]
            return members
        except Exception as e:
            raise Exception(f"Error fetching all members: {str(e)}")

    def fetch_users_by_criteria(self, field: str, value: any, operator: str = "==") -> List[Member]:
        """
        Fetch users from the members collection based on custom criteria.

        Args:
            field (str): The field name to filter by
            value (any): The value to match
            operator (str): The comparison operator (==, <, >, <=, >=, !=)

        Returns:
            List[Member]: List of member objects matching the criteria

        Raises:
            Exception: If there's an error accessing the database
            ValueError: If an invalid operator is provided
        """
        valid_operators = ["==", "<", ">", "<=", ">=", "!="]
        if operator not in valid_operators:
            raise ValueError(
                f"Invalid operator '{operator}'. Must be one of: {', '.join(valid_operators)}"
            )

        try:
            query = self.db.collection(self.COLLECTION_NAME).where(field, operator, value)
            docs = query.stream()
            members = [self._document_to_member(doc) for doc in docs]
            return members
        except Exception as e:
            raise Exception(
                f"Error fetching members with criteria {field} {operator} {value}: {str(e)}"
            )

    def create_user(self, member_data: MemberCreate) -> Member:
        """
        Create a new user in the members collection.

        Args:
            member_data (MemberCreate): The member data to create

        Returns:
            Member: The created member object with ID

        Raises:
            Exception: If there's an error creating the member
        """
        try:
            now = datetime.now()
            data = {
                **member_data.model_dump(),
                "created_at": now,
                "updated_at": now,
            }

            doc_ref = self.db.collection(self.COLLECTION_NAME).document()
            doc_ref.set(data)

            return Member(id=doc_ref.id, created_at=now, updated_at=now, **member_data.model_dump())
        except Exception as e:
            raise Exception(f"Error creating member: {str(e)}")

    def update_user(self, member_id: str, update_data: MemberUpdate) -> Optional[Member]:
        """
        Update an existing user in the members collection.

        Args:
            member_id (str): The ID of the member to update
            update_data (MemberUpdate): The data to update

        Returns:
            Optional[Member]: The updated member object, or None if member doesn't exist

        Raises:
            Exception: If there's an error updating the member
        """
        try:
            doc_ref = self.db.collection(self.COLLECTION_NAME).document(member_id)

            # Check if document exists
            if not doc_ref.get().exists:
                return None

            update_fields = {
                k: v for k, v in update_data.model_dump().items() if v is not None
            }
            update_fields["updated_at"] = datetime.now()

            doc_ref.update(update_fields)

            # Fetch and return the updated member
            return self.fetch_user_by_id(member_id)
        except Exception as e:
            raise Exception(f"Error updating member with ID {member_id}: {str(e)}")

    def delete_user(self, member_id: str) -> bool:
        """
        Delete a user from the members collection.

        Args:
            member_id (str): The ID of the member to delete

        Returns:
            bool: True if member was deleted, False if member doesn't exist

        Raises:
            Exception: If there's an error deleting the member
        """
        try:
            doc_ref = self.db.collection(self.COLLECTION_NAME).document(member_id)

            # Check if document exists
            if not doc_ref.get().exists:
                return False

            doc_ref.delete()
            return True
        except Exception as e:
            raise Exception(f"Error deleting member with ID {member_id}: {str(e)}")

    @staticmethod
    def _document_to_member(doc: DocumentSnapshot) -> Member:
        """
        Convert a Firestore document snapshot to a Member object.

        Args:
            doc (DocumentSnapshot): The Firestore document snapshot

        Returns:
            Member: The converted Member object
        """
        data = doc.to_dict()

        # Handle preferences
        preferences_data = data.get("preferences")
        from app.models.member import UserPreferences
        preferences = UserPreferences(**preferences_data) if preferences_data else None

        return Member(
            id=doc.id,
            email=data.get("email"),
            display_name=data.get("display_name"),
            photo_url=data.get("photo_url"),
            phone=data.get("phone"),
            address=data.get("address"),
            is_email_verified=data.get("is_email_verified", False),
            created_at=data.get("created_at"),
            last_sign_in_at=data.get("last_sign_in_at"),
            preferences=preferences,
        )


# Convenience function to create a service instance
def get_member_service() -> MemberService:
    """Create and return a member service instance."""
    return MemberService()
