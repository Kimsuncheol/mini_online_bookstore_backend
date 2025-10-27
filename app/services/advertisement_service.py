"""
Advertisement Service

Provides business logic and database operations for managing advertisements.
Includes CRUD operations and filtering for hero carousel books.
"""

from typing import List, Optional, Any
from datetime import datetime
from google.cloud.firestore import DocumentSnapshot
from app.models.advertisement import (
    Advertisement,
    AdvertisementCreate,
    AdvertisementUpdate,
    HeroCarouselBook,
)
from app.utils.firebase_config import get_firestore_client


class AdvertisementService:
    """Service class for advertisement-related database operations."""

    ADVERTISEMENTS_COLLECTION = "advertisements"

    def __init__(self):
        """Initialize the advertisement service with Firestore client."""
        self.db: Any = get_firestore_client()

    # ==================== ADVERTISEMENT CRUD OPERATIONS ====================

    def create_advertisement(self, ad_data: AdvertisementCreate) -> Advertisement:
        """
        Create a new advertisement in the bookstore.

        Args:
            ad_data (AdvertisementCreate): The advertisement data to create

        Returns:
            Advertisement: The created advertisement object with ID

        Raises:
            Exception: If there's an error creating the advertisement
        """
        try:
            now = datetime.now()
            data = {
                **ad_data.model_dump(),
                "created_at": now,
                "updated_at": now,
            }

            # Convert datetime fields to Firestore timestamps if present
            if data.get("start_date"):
                data["start_date"] = data["start_date"]
            if data.get("end_date"):
                data["end_date"] = data["end_date"]

            doc_ref = self.db.collection(self.ADVERTISEMENTS_COLLECTION).document()
            doc_ref.set(data)

            return Advertisement(
                id=doc_ref.id,
                created_at=now,
                updated_at=now,
                **ad_data.model_dump(),
            )
        except Exception as e:
            raise Exception(f"Error creating advertisement: {str(e)}")

    def get_advertisement_by_id(self, ad_id: str) -> Optional[Advertisement]:
        """
        Fetch an advertisement by its ID.

        Args:
            ad_id (str): The unique identifier of the advertisement

        Returns:
            Optional[Advertisement]: Advertisement object if found, None otherwise

        Raises:
            Exception: If there's an error fetching the advertisement
        """
        try:
            doc = self.db.collection(self.ADVERTISEMENTS_COLLECTION).document(ad_id).get()

            if doc.exists:
                return self._document_to_advertisement(doc)
            else:
                return None
        except Exception as e:
            raise Exception(f"Error fetching advertisement with ID {ad_id}: {str(e)}")

    def get_all_advertisements(self, limit: Optional[int] = None) -> List[Advertisement]:
        """
        Fetch all advertisements from the bookstore.

        Args:
            limit (Optional[int]): Maximum number of advertisements to return

        Returns:
            List[Advertisement]: List of all advertisement objects

        Raises:
            Exception: If there's an error fetching advertisements
        """
        try:
            query = self.db.collection(self.ADVERTISEMENTS_COLLECTION)

            if limit:
                query = query.limit(limit)

            docs = query.stream()
            advertisements = [self._document_to_advertisement(doc) for doc in docs]
            return advertisements
        except Exception as e:
            raise Exception(f"Error fetching all advertisements: {str(e)}")

    def get_active_advertisements(self, limit: Optional[int] = None) -> List[Advertisement]:
        """
        Fetch active advertisements (for hero carousel).

        Args:
            limit (Optional[int]): Maximum number of advertisements to return

        Returns:
            List[Advertisement]: List of active advertisement objects ordered by display_order

        Raises:
            Exception: If there's an error fetching advertisements
        """
        try:
            now = datetime.now()
            query = (
                self.db.collection(self.ADVERTISEMENTS_COLLECTION)
                .where("is_active", "==", True)
                .order_by("display_order")
            )

            if limit:
                query = query.limit(limit)

            docs = query.stream()
            advertisements = []

            for doc in docs:
                ad = self._document_to_advertisement(doc)

                # Check if advertisement is within date range
                if ad.start_date and ad.start_date > now:
                    continue
                if ad.end_date and ad.end_date < now:
                    continue

                advertisements.append(ad)

            return advertisements
        except Exception as e:
            raise Exception(f"Error fetching active advertisements: {str(e)}")

    def get_hero_carousel_books(self, limit: Optional[int] = None) -> List[HeroCarouselBook]:
        """
        Fetch hero carousel books (client-facing format).

        Args:
            limit (Optional[int]): Maximum number of books to return

        Returns:
            List[HeroCarouselBook]: List of hero carousel book objects

        Raises:
            Exception: If there's an error fetching books
        """
        try:
            advertisements = self.get_active_advertisements(limit=limit)

            # Convert to HeroCarouselBook format
            carousel_books = []
            for ad in advertisements:
                carousel_book = HeroCarouselBook(
                    id=ad.id,
                    title=ad.title,
                    author=ad.author,
                    description=ad.description,
                    price=ad.price,
                    pageCount=ad.page_count,
                    originalPrice=ad.original_price,
                    coverImageUrl=ad.cover_image_url,
                )
                carousel_books.append(carousel_book)

            return carousel_books
        except Exception as e:
            raise Exception(f"Error fetching hero carousel books: {str(e)}")

    def update_advertisement(
        self, ad_id: str, update_data: AdvertisementUpdate
    ) -> Optional[Advertisement]:
        """
        Update an existing advertisement.

        Args:
            ad_id (str): The ID of the advertisement to update
            update_data (AdvertisementUpdate): The data to update

        Returns:
            Optional[Advertisement]: The updated advertisement object, or None if not found

        Raises:
            Exception: If there's an error updating the advertisement
        """
        try:
            doc_ref = self.db.collection(self.ADVERTISEMENTS_COLLECTION).document(ad_id)

            # Check if document exists
            if not doc_ref.get().exists:
                return None

            update_fields = {
                k: v for k, v in update_data.model_dump().items() if v is not None
            }
            update_fields["updated_at"] = datetime.now()

            doc_ref.update(update_fields)

            # Fetch and return the updated advertisement
            return self.get_advertisement_by_id(ad_id)
        except Exception as e:
            raise Exception(f"Error updating advertisement with ID {ad_id}: {str(e)}")

    def delete_advertisement(self, ad_id: str) -> bool:
        """
        Delete an advertisement from the bookstore.

        Args:
            ad_id (str): The ID of the advertisement to delete

        Returns:
            bool: True if advertisement was deleted, False if doesn't exist

        Raises:
            Exception: If there's an error deleting the advertisement
        """
        try:
            doc_ref = self.db.collection(self.ADVERTISEMENTS_COLLECTION).document(ad_id)

            # Check if document exists
            if not doc_ref.get().exists:
                return False

            doc_ref.delete()
            return True
        except Exception as e:
            raise Exception(f"Error deleting advertisement with ID {ad_id}: {str(e)}")

    def toggle_active_status(self, ad_id: str) -> Optional[Advertisement]:
        """
        Toggle the active status of an advertisement.

        Args:
            ad_id (str): The ID of the advertisement

        Returns:
            Optional[Advertisement]: Updated advertisement object, or None if not found

        Raises:
            Exception: If there's an error toggling status
        """
        try:
            ad = self.get_advertisement_by_id(ad_id)
            if not ad:
                return None

            update_data = AdvertisementUpdate(is_active=not ad.is_active)
            return self.update_advertisement(ad_id, update_data)
        except Exception as e:
            raise Exception(f"Error toggling active status for advertisement {ad_id}: {str(e)}")

    def reorder_advertisements(self, ad_id: str, new_order: int) -> Optional[Advertisement]:
        """
        Change the display order of an advertisement.

        Args:
            ad_id (str): The ID of the advertisement
            new_order (int): The new display order

        Returns:
            Optional[Advertisement]: Updated advertisement object, or None if not found

        Raises:
            Exception: If there's an error reordering
        """
        try:
            update_data = AdvertisementUpdate(display_order=new_order)
            return self.update_advertisement(ad_id, update_data)
        except Exception as e:
            raise Exception(f"Error reordering advertisement {ad_id}: {str(e)}")

    # ==================== HELPER METHODS ====================

    @staticmethod
    def _document_to_advertisement(doc: DocumentSnapshot) -> Advertisement:
        """Convert a Firestore document snapshot to an Advertisement object."""
        data = doc.to_dict()
        return Advertisement(
            id=doc.id,
            book_id=data.get("book_id"),
            title=data.get("title"),
            author=data.get("author"),
            description=data.get("description"),
            price=data.get("price"),
            page_count=data.get("page_count"),
            original_price=data.get("original_price"),
            cover_image_url=data.get("cover_image_url"),
            is_active=data.get("is_active", True),
            display_order=data.get("display_order", 0),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


# Convenience function to create a service instance
def get_advertisement_service() -> AdvertisementService:
    """Create and return an advertisement service instance."""
    return AdvertisementService()
