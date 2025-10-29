"""
Like Service

Provides business logic and database operations for managing user's liked books.
Includes operations for adding, removing, and querying liked books.
"""

from typing import List, Optional, Any
from datetime import datetime
from google.cloud.firestore import DocumentSnapshot
from app.models.like import (
    Like,
    LikeCreate,
    LikeResponse,
    LikeStatusResponse,
    LikeCountResponse,
)
from app.utils.firebase_config import get_firestore_client


class LikeService:
    """Service class for like-related database operations."""

    LIKES_ROOT_COLLECTION = "likes"
    LIKES_SUBCOLLECTION = "likes"

    def __init__(self):
        """Initialize the like service with Firestore client."""
        self.db: Any = get_firestore_client()

    # ==================== HELPER METHODS FOR PATH BUILDING ====================

    def _get_user_likes_ref(self, user_email: str):
        """Get reference to user's likes subcollection."""
        return (
            self.db.collection(self.LIKES_ROOT_COLLECTION)
            .document(user_email)
            .collection(self.LIKES_SUBCOLLECTION)
        )

    # ==================== LIKE CRUD OPERATIONS ====================

    def create_like(self, like_data: LikeCreate) -> Like:
        """
        Add a book to user's liked books.

        Args:
            like_data (LikeCreate): The like data to create

        Returns:
            Like: The created like object with ID

        Raises:
            Exception: If there's an error creating the like or if already liked
        """
        try:
            # Check if the book is already liked by this user
            existing_like = self.get_like_by_book_and_user(
                like_data.book_id, like_data.user_email
            )
            if existing_like:
                raise ValueError(
                    f"Book '{like_data.book_id}' is already liked by user '{like_data.user_email}'"
                )

            now = datetime.now()
            data = {
                **like_data.model_dump(),
                "created_at": now,
            }

            doc_ref = self._get_user_likes_ref(like_data.user_email).document()
            doc_ref.set(data)

            return Like(
                id=doc_ref.id,
                created_at=now,
                **like_data.model_dump(),
            )
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Error creating like: {str(e)}")

    def remove_like(self, like_id: str, user_email: str) -> bool:
        """
        Remove a like from the user's liked books.

        Args:
            like_id (str): The ID of the like to remove
            user_email (str): The user's email address

        Returns:
            bool: True if like was removed, False if doesn't exist

        Raises:
            Exception: If there's an error removing the like
        """
        try:
            doc_ref = self._get_user_likes_ref(user_email).document(like_id)

            # Check if document exists
            if not doc_ref.get().exists:
                return False

            doc_ref.delete()
            return True
        except Exception as e:
            raise Exception(f"Error removing like with ID {like_id}: {str(e)}")

    def remove_like_by_book_and_user(self, book_id: str, user_email: str) -> bool:
        """
        Remove a like by book ID and user email.

        Args:
            book_id (str): The ID of the book
            user_email (str): The user's email address

        Returns:
            bool: True if like was removed, False if doesn't exist

        Raises:
            Exception: If there's an error removing the like
        """
        try:
            like = self.get_like_by_book_and_user(book_id, user_email)
            if not like:
                return False

            return self.remove_like(like.id, user_email)
        except Exception as e:
            raise Exception(
                f"Error removing like for book '{book_id}' by user '{user_email}': {str(e)}"
            )

    def get_like_by_id(self, like_id: str, user_email: str) -> Optional[Like]:
        """
        Fetch a like by its ID.

        Args:
            like_id (str): The unique identifier of the like
            user_email (str): The user's email address

        Returns:
            Optional[Like]: Like object if found, None otherwise

        Raises:
            Exception: If there's an error fetching the like
        """
        try:
            doc = self._get_user_likes_ref(user_email).document(like_id).get()

            if doc.exists:
                return self._document_to_like(doc)
            else:
                return None
        except Exception as e:
            raise Exception(f"Error fetching like with ID {like_id}: {str(e)}")

    def get_like_by_book_and_user(self, book_id: str, user_email: str) -> Optional[Like]:
        """
        Fetch a like by book ID and user email.

        Args:
            book_id (str): The ID of the book
            user_email (str): The user's email address

        Returns:
            Optional[Like]: Like object if found, None otherwise

        Raises:
            Exception: If there's an error fetching the like
        """
        try:
            docs = (
                self._get_user_likes_ref(user_email)
                .where("book_id", "==", book_id)
                .limit(1)
                .stream()
            )

            for doc in docs:
                return self._document_to_like(doc)

            return None
        except Exception as e:
            raise Exception(
                f"Error fetching like for book '{book_id}' by user '{user_email}': {str(e)}"
            )

    def get_user_likes(self, user_email: str, limit: Optional[int] = None) -> List[Like]:
        """
        Fetch all liked books for a user.

        Args:
            user_email (str): The user's email address
            limit (Optional[int]): Maximum number of likes to return

        Returns:
            List[Like]: List of user's liked books

        Raises:
            Exception: If there's an error fetching likes
        """
        try:
            query = (
                self._get_user_likes_ref(user_email)
                .order_by("created_at", direction="DESCENDING")
            )

            if limit:
                query = query.limit(limit)

            docs = query.stream()
            likes = [self._document_to_like(doc) for doc in docs]
            return likes
        except Exception as e:
            raise Exception(f"Error fetching likes for user '{user_email}': {str(e)}")

    def get_book_likes(self, book_id: str, limit: Optional[int] = None) -> List[Like]:
        """
        Fetch all likes for a specific book.

        Args:
            book_id (str): The ID of the book
            limit (Optional[int]): Maximum number of likes to return

        Returns:
            List[Like]: List of likes for the book

        Raises:
            Exception: If there's an error fetching likes
        """
        try:
            likes = []
            # Get all users' documents in likes collection
            users_docs = self.db.collection(self.LIKES_ROOT_COLLECTION).stream()

            for user_doc in users_docs:
                user_email = user_doc.id
                # Query likes subcollection for this user
                query = (
                    self._get_user_likes_ref(user_email)
                    .where("book_id", "==", book_id)
                    .stream()
                )
                for doc in query:
                    likes.append(self._document_to_like(doc))

            # Sort by created_at descending
            likes.sort(key=lambda x: x.created_at or datetime.now(), reverse=True)

            if limit:
                likes = likes[:limit]

            return likes
        except Exception as e:
            raise Exception(f"Error fetching likes for book '{book_id}': {str(e)}")

    # ==================== LIKE STATUS AND COUNT OPERATIONS ====================

    def is_book_liked_by_user(self, book_id: str, user_email: str) -> LikeStatusResponse:
        """
        Check if a book is liked by a user.

        Args:
            book_id (str): The ID of the book
            user_email (str): The user's email address

        Returns:
            LikeStatusResponse: Object containing like status and like ID

        Raises:
            Exception: If there's an error checking like status
        """
        try:
            like = self.get_like_by_book_and_user(book_id, user_email)
            if like:
                return LikeStatusResponse(is_liked=True, like_id=like.id)
            else:
                return LikeStatusResponse(is_liked=False, like_id=None)
        except Exception as e:
            raise Exception(
                f"Error checking like status for book '{book_id}' by user '{user_email}': {str(e)}"
            )

    def get_book_like_count(self, book_id: str) -> LikeCountResponse:
        """
        Get the total number of likes for a book.

        Args:
            book_id (str): The ID of the book

        Returns:
            LikeCountResponse: Object containing book ID and like count

        Raises:
            Exception: If there's an error counting likes
        """
        try:
            like_count = 0
            # Get all users' documents in likes collection
            users_docs = self.db.collection(self.LIKES_ROOT_COLLECTION).stream()

            for user_doc in users_docs:
                user_email = user_doc.id
                # Query likes subcollection for this user
                docs = (
                    self._get_user_likes_ref(user_email)
                    .where("book_id", "==", book_id)
                    .stream()
                )
                like_count += sum(1 for _ in docs)

            return LikeCountResponse(book_id=book_id, like_count=like_count)
        except Exception as e:
            raise Exception(f"Error counting likes for book '{book_id}': {str(e)}")

    def get_user_like_count(self, user_email: str) -> int:
        """
        Get the total number of books liked by a user.

        Args:
            user_email (str): The user's email address

        Returns:
            int: Number of books liked by the user

        Raises:
            Exception: If there's an error counting likes
        """
        try:
            docs = self._get_user_likes_ref(user_email).stream()

            return sum(1 for _ in docs)
        except Exception as e:
            raise Exception(f"Error counting likes for user '{user_email}': {str(e)}")

    # ==================== TOGGLE OPERATION ====================

    def toggle_like(self, like_data: LikeCreate) -> dict:
        """
        Toggle like status (add if not liked, remove if liked).

        Args:
            like_data (LikeCreate): The like data

        Returns:
            dict: Object containing action taken ('added' or 'removed') and like data

        Raises:
            Exception: If there's an error toggling like
        """
        try:
            existing_like = self.get_like_by_book_and_user(
                like_data.book_id, like_data.user_email
            )

            if existing_like:
                # Unlike: remove the like
                self.remove_like(existing_like.id)
                return {
                    "action": "removed",
                    "message": f"Book '{like_data.book_id}' removed from likes",
                    "is_liked": False,
                }
            else:
                # Like: add the like
                new_like = self.create_like(like_data)
                return {
                    "action": "added",
                    "message": f"Book '{like_data.book_id}' added to likes",
                    "is_liked": True,
                    "like": new_like.model_dump(),
                }
        except Exception as e:
            raise Exception(f"Error toggling like: {str(e)}")

    # ==================== HELPER METHODS ====================

    @staticmethod
    def _document_to_like(doc: DocumentSnapshot) -> Like:
        """Convert a Firestore document snapshot to a Like object."""
        data = doc.to_dict()
        return Like(
            id=doc.id,
            book_id=data.get("book_id"),
            title=data.get("title"),
            user_email=data.get("user_email"),
            price=data.get("price"),
            original_price=data.get("original_price"),
            cover_image_url=data.get("cover_image_url"),
            created_at=data.get("created_at"),
        )

    @staticmethod
    def like_to_response(like: Like) -> LikeResponse:
        """Convert a Like object to LikeResponse (client-facing format)."""
        return LikeResponse(
            bookId=like.book_id,
            title=like.title,
            userEmail=like.user_email,
            price=like.price,
            originalPrice=like.original_price,
            coverImageUrl=like.cover_image_url,
            createdAt=like.created_at,
        )


# Convenience function to create a service instance
def get_like_service() -> LikeService:
    """Create and return a like service instance."""
    return LikeService()
