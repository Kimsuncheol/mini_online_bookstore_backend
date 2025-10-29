"""
Author Service

Provides business logic and database operations for managing authors in the
`authors` collection with author-specific fields and statistics.
"""

from typing import Any, List, Optional
from datetime import datetime
from google.cloud.firestore import DocumentSnapshot
from app.models.author import (
    Author,
    AuthorCreate,
    AuthorUpdate,
    AuthorProfile,
    AuthorStatistics,
    AuthorPreferences,
)
from app.utils.firebase_config import get_firestore_client


class AuthorService:
    """Service class for author-related database operations."""

    COLLECTION_NAME = "authors"

    def __init__(self):
        """Initialize the author service with Firestore client."""
        self.db: Any = get_firestore_client()

    # ==================== AUTHOR CRUD OPERATIONS ====================

    def fetch_author_by_id(self, author_id: str) -> Optional[Author]:
        """
        Fetch an author from the authors collection by author ID.

        Args:
            author_id (str): The unique identifier of the author document in Firestore

        Returns:
            Optional[Author]: Author object if found, None otherwise

        Raises:
            Exception: If there's an error accessing the database
        """
        try:
            doc = self.db.collection(self.COLLECTION_NAME).document(author_id).get()

            if doc.exists:
                return self._document_to_author(doc)
            else:
                return None
        except Exception as e:
            raise Exception(f"Error fetching author with ID {author_id}: {str(e)}")

    def fetch_author_by_email(self, email: str) -> Optional[Author]:
        """
        Fetch an author from the authors collection by email address.

        Args:
            email (str): The email address of the author

        Returns:
            Optional[Author]: Author object if found, None otherwise

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
                return self._document_to_author(doc)
            return None
        except Exception as e:
            raise Exception(f"Error fetching author with email {email}: {str(e)}")

    def fetch_all_authors(self) -> List[Author]:
        """
        Fetch all authors from the authors collection.

        Returns:
            List[Author]: List of all author objects

        Raises:
            Exception: If there's an error accessing the database
        """
        try:
            docs = self.db.collection(self.COLLECTION_NAME).stream()
            authors = [self._document_to_author(doc) for doc in docs]
            return authors
        except Exception as e:
            raise Exception(f"Error fetching all authors: {str(e)}")

    def fetch_verified_authors(self) -> List[Author]:
        """
        Fetch all verified authors from the authors collection.

        Returns:
            List[Author]: List of verified author objects

        Raises:
            Exception: If there's an error accessing the database
        """
        try:
            docs = (
                self.db.collection(self.COLLECTION_NAME)
                .where("isVerified", "==", True)
                .stream()
            )
            authors = [self._document_to_author(doc) for doc in docs]
            return authors
        except Exception as e:
            raise Exception(f"Error fetching verified authors: {str(e)}")

    def fetch_authors_by_criteria(self, field: str, value: any, operator: str = "==") -> List[Author]:
        """
        Fetch authors from the authors collection based on custom criteria.

        Args:
            field (str): The field name to filter by
            value (any): The value to match
            operator (str): The comparison operator (==, <, >, <=, >=, !=)

        Returns:
            List[Author]: List of author objects matching the criteria

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
            storage_field = self._map_storage_field(field)
            query = self.db.collection(self.COLLECTION_NAME).where(storage_field, operator, value)
            docs = query.stream()
            authors = [self._document_to_author(doc) for doc in docs]
            return authors
        except Exception as e:
            raise Exception(
                f"Error fetching authors with criteria {field} {operator} {value}: {str(e)}"
            )

    @staticmethod
    def _map_storage_field(field: str) -> str:
        """
        Map internal snake_case field names to stored Firestore field names (camelCase).
        """
        field_mapping = {
            "display_name": "displayName",
            "displayName": "displayName",
            "photo_url": "photoURL",
            "photoURL": "photoURL",
            "is_email_verified": "isEmailVerified",
            "isEmailVerified": "isEmailVerified",
            "social_links": "socialLinks",
            "socialLinks": "socialLinks",
            "is_verified": "isVerified",
            "isVerified": "isVerified",
            "verification_date": "verificationDate",
            "verificationDate": "verificationDate",
            "verification_badge": "verificationBadge",
            "verificationBadge": "verificationBadge",
            "total_books_published": "totalBooksPublished",
            "totalBooksPublished": "totalBooksPublished",
            "total_readers_reached": "totalReadersReached",
            "totalReadersReached": "totalReadersReached",
            "average_rating": "averageRating",
            "averageRating": "averageRating",
            "created_at": "createdAt",
            "createdAt": "createdAt",
            "lastSignInAt": "lastSignInAt",
            "last_sign_in_at": "lastSignInAt",
        }
        return field_mapping.get(field, field)

    def create_author(self, author_data: AuthorCreate) -> Author:
        """
        Create a new author in the authors collection.

        Args:
            author_data (AuthorCreate): The author data to create

        Returns:
            Author: The created author object with ID

        Raises:
            Exception: If there's an error creating the author
        """
        try:
            now = datetime.now()
            data = author_data.model_dump(by_alias=True, exclude_none=True)
            data.setdefault("createdAt", now)
            data.setdefault("lastSignInAt", now)
            data.setdefault("isEmailVerified", False)
            data.setdefault("role", "author")
            data.setdefault("isVerified", False)
            data.setdefault("verificationBadge", False)
            data.setdefault("totalBooksPublished", 0)
            data.setdefault("totalReadersReached", 0)
            data.setdefault("averageRating", 0.0)
            if data.get("preferences") is None:
                data["preferences"] = {
                    "emailNotifications": True,
                    "marketingEmails": False,
                }
            data["updatedAt"] = now

            doc_ref = self.db.collection(self.COLLECTION_NAME).document()
            doc_ref.set(data)

            return Author(
                id=doc_ref.id,
                email=data["email"],
                display_name=data.get("displayName"),
                photo_url=data.get("photoURL"),
                role=data.get("role", "author"),
                is_email_verified=data.get("isEmailVerified", False),
                bio=data.get("bio"),
                website=data.get("website"),
                social_links=data.get("socialLinks"),
                phone=data.get("phone"),
                address=data.get("address"),
                is_verified=data.get("isVerified", False),
                verification_badge=data.get("verificationBadge", False),
                total_books_published=data.get("totalBooksPublished", 0),
                total_readers_reached=data.get("totalReadersReached", 0),
                average_rating=data.get("averageRating", 0.0),
                preferences=data.get("preferences"),
                created_at=data["createdAt"],
                last_sign_in_at=data.get("lastSignInAt"),
            )
        except Exception as e:
            raise Exception(f"Error creating author: {str(e)}")

    def update_author(self, author_id: str, update_data: AuthorUpdate) -> Optional[Author]:
        """
        Update an existing author in the authors collection.

        Args:
            author_id (str): The ID of the author to update
            update_data (AuthorUpdate): The data to update

        Returns:
            Optional[Author]: The updated author object, or None if author doesn't exist

        Raises:
            Exception: If there's an error updating the author
        """
        try:
            doc_ref = self.db.collection(self.COLLECTION_NAME).document(author_id)

            # Check if document exists
            if not doc_ref.get().exists:
                return None

            update_fields = update_data.model_dump(by_alias=True, exclude_none=True)
            update_fields["updatedAt"] = datetime.now()

            doc_ref.update(update_fields)

            # Fetch and return the updated author
            return self.fetch_author_by_id(author_id)
        except Exception as e:
            raise Exception(f"Error updating author with ID {author_id}: {str(e)}")

    def delete_author(self, author_id: str) -> bool:
        """
        Delete an author from the authors collection.

        Args:
            author_id (str): The ID of the author to delete

        Returns:
            bool: True if the author was deleted, False if the author doesn't exist

        Raises:
            Exception: If there's an error deleting the author
        """
        try:
            doc_ref = self.db.collection(self.COLLECTION_NAME).document(author_id)

            # Check if document exists
            if not doc_ref.get().exists:
                return False

            doc_ref.delete()
            return True
        except Exception as e:
            raise Exception(f"Error deleting author with ID {author_id}: {str(e)}")

    # ==================== AUTHOR VERIFICATION ====================

    def verify_author(self, author_id: str) -> Optional[Author]:
        """
        Verify an author and add verification badge.

        Args:
            author_id (str): The ID of the author to verify

        Returns:
            Optional[Author]: The updated author object, or None if author doesn't exist

        Raises:
            Exception: If there's an error verifying the author
        """
        try:
            doc_ref = self.db.collection(self.COLLECTION_NAME).document(author_id)

            if not doc_ref.get().exists:
                return None

            update_fields = {
                "isVerified": True,
                "verificationBadge": True,
                "verificationDate": datetime.now(),
                "updatedAt": datetime.now(),
            }

            doc_ref.update(update_fields)

            return self.fetch_author_by_id(author_id)
        except Exception as e:
            raise Exception(f"Error verifying author with ID {author_id}: {str(e)}")

    # ==================== AUTHOR STATISTICS ====================

    def get_author_statistics(self, author_id: str) -> Optional[AuthorStatistics]:
        """
        Get author statistics.

        Args:
            author_id (str): The ID of the author

        Returns:
            Optional[AuthorStatistics]: Author statistics object, or None if author doesn't exist

        Raises:
            Exception: If there's an error fetching statistics
        """
        try:
            author = self.fetch_author_by_id(author_id)
            if not author:
                return None

            return AuthorStatistics(
                total_books_published=author.total_books_published,
                total_readers_reached=author.total_readers_reached,
                average_rating=author.average_rating,
                total_reviews=0,
                total_followers=0,
            )
        except Exception as e:
            raise Exception(f"Error getting author statistics for author {author_id}: {str(e)}")

    def get_author_profile(self, author_id: str) -> Optional[AuthorProfile]:
        """
        Get author profile data for public display.

        Args:
            author_id (str): The ID of the author

        Returns:
            Optional[AuthorProfile]: Author profile object, or None if author doesn't exist

        Raises:
            Exception: If there's an error fetching the profile
        """
        try:
            author = self.fetch_author_by_id(author_id)
            if not author:
                return None

            return AuthorProfile(
                id=author.id,
                display_name=author.display_name or author.email.split("@")[0],
                email=author.email,
                photo_url=author.photo_url,
                bio=author.bio,
                website=author.website,
                is_verified=author.is_verified,
                total_books_published=author.total_books_published,
                average_rating=author.average_rating,
                created_at=author.created_at,
            )
        except Exception as e:
            raise Exception(f"Error getting author profile for author {author_id}: {str(e)}")

    def update_author_statistics(
        self,
        author_id: str,
        books_published: Optional[int] = None,
        readers_reached: Optional[int] = None,
        average_rating: Optional[float] = None,
    ) -> Optional[Author]:
        """
        Update author statistics.

        Args:
            author_id (str): The ID of the author
            books_published (Optional[int]): Number of books published
            readers_reached (Optional[int]): Number of readers reached
            average_rating (Optional[float]): Average rating

        Returns:
            Optional[Author]: The updated author object, or None if author doesn't exist

        Raises:
            Exception: If there's an error updating statistics
        """
        try:
            doc_ref = self.db.collection(self.COLLECTION_NAME).document(author_id)

            if not doc_ref.get().exists:
                return None

            update_fields = {"updatedAt": datetime.now()}
            if books_published is not None:
                update_fields["totalBooksPublished"] = books_published
            if readers_reached is not None:
                update_fields["totalReadersReached"] = readers_reached
            if average_rating is not None:
                update_fields["averageRating"] = max(0.0, min(5.0, average_rating))

            doc_ref.update(update_fields)

            return self.fetch_author_by_id(author_id)
        except Exception as e:
            raise Exception(f"Error updating author statistics for author {author_id}: {str(e)}")

    # ==================== HELPER METHODS ====================

    @staticmethod
    def _document_to_author(doc: DocumentSnapshot) -> Author:
        """
        Convert a Firestore document snapshot to an Author object.

        Args:
            doc (DocumentSnapshot): The Firestore document snapshot

        Returns:
            Author: The converted Author object
        """
        data = doc.to_dict() or {}

        # Handle preferences with backward compatibility for casing
        preferences_data = data.get("preferences")
        preferences = AuthorPreferences(**preferences_data) if preferences_data else None

        display_name = data.get("displayName") or data.get("display_name")
        photo_url = data.get("photoURL") or data.get("photo_url")
        bio = data.get("bio")
        website = data.get("website")
        social_links = data.get("socialLinks") or data.get("social_links")
        phone = data.get("phone")
        address = data.get("address")
        created_at = data.get("createdAt") or data.get("created_at") or datetime.now()
        last_sign_in_at = data.get("lastSignInAt") or data.get("last_sign_in_at")
        is_email_verified = data.get("isEmailVerified", data.get("is_email_verified", False))
        is_verified = data.get("isVerified", data.get("is_verified", False))
        verification_date = data.get("verificationDate") or data.get("verification_date")
        verification_badge = data.get("verificationBadge", data.get("verification_badge", False))
        total_books_published = data.get("totalBooksPublished", data.get("total_books_published", 0))
        total_readers_reached = data.get("totalReadersReached", data.get("total_readers_reached", 0))
        average_rating = data.get("averageRating", data.get("average_rating", 0.0))
        role = data.get("role", "author")

        return Author(
            id=doc.id,
            email=data.get("email"),
            display_name=display_name,
            photo_url=photo_url,
            role=role,
            is_email_verified=is_email_verified,
            bio=bio,
            website=website,
            social_links=social_links,
            phone=phone,
            address=address,
            is_verified=is_verified,
            verification_date=verification_date,
            verification_badge=verification_badge,
            total_books_published=total_books_published,
            total_readers_reached=total_readers_reached,
            average_rating=average_rating,
            preferences=preferences,
            created_at=created_at,
            last_sign_in_at=last_sign_in_at,
        )


# Convenience function to create a service instance
def get_author_service() -> AuthorService:
    """Create and return an author service instance."""
    return AuthorService()
