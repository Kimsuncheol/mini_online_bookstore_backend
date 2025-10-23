"""
Cart Service

Provides business logic and database operations for managing user shopping carts.

Database structure:
- carts (collection)
  └── {userId} (document)
      └── items (subcollection)
          └── {itemId} (document)
"""

from typing import List, Optional, Any
from datetime import datetime
from google.cloud import firestore
from google.cloud.firestore import DocumentSnapshot
from app.models.cart_item import CartItem, CartItemCreate, CartItemUpdate
from app.utils.firebase_config import get_firestore_client


class CartService:
    """Service class for cart-related database operations."""

    CARTS_COLLECTION = "carts"
    ITEMS_SUBCOLLECTION = "items"

    def __init__(self):
        """Initialize the cart service with Firestore client."""
        self.db: Any = get_firestore_client()

    def add_item_to_cart(self, user_id: str, item_data: CartItemCreate) -> CartItem:
        """
        Add an item to a user's shopping cart.

        Args:
            user_id (str): The unique identifier of the user
            item_data (CartItemCreate): The cart item data to add

        Returns:
            CartItem: The created cart item with ID

        Raises:
            Exception: If there's an error adding the item to the cart
        """
        try:
            items_ref = (
                self.db.collection(self.CARTS_COLLECTION)
                .document(user_id)
                .collection(self.ITEMS_SUBCOLLECTION)
            )

            # Add the item to the subcollection
            doc_ref = items_ref.document()
            doc_ref.set(item_data.model_dump())

            return CartItem(id=doc_ref.id, **item_data.model_dump())
        except Exception as e:
            raise Exception(f"Error adding item to cart for user {user_id}: {str(e)}")

    def get_cart_item(self, user_id: str, item_id: str) -> Optional[CartItem]:
        """
        Fetch a specific item from a user's shopping cart.

        Args:
            user_id (str): The unique identifier of the user
            item_id (str): The unique identifier of the cart item

        Returns:
            Optional[CartItem]: CartItem object if found, None otherwise

        Raises:
            Exception: If there's an error fetching the item
        """
        try:
            doc = (
                self.db.collection(self.CARTS_COLLECTION)
                .document(user_id)
                .collection(self.ITEMS_SUBCOLLECTION)
                .document(item_id)
                .get()
            )

            if doc.exists:
                return self._document_to_cart_item(doc)
            else:
                return None
        except Exception as e:
            raise Exception(
                f"Error fetching cart item {item_id} for user {user_id}: {str(e)}"
            )

    def get_user_cart(self, user_id: str) -> List[CartItem]:
        """
        Fetch all items from a user's shopping cart.

        Args:
            user_id (str): The unique identifier of the user

        Returns:
            List[CartItem]: List of all cart items for the user

        Raises:
            Exception: If there's an error fetching the cart
        """
        try:
            docs = (
                self.db.collection(self.CARTS_COLLECTION)
                .document(user_id)
                .collection(self.ITEMS_SUBCOLLECTION)
                .stream()
            )

            cart_items = [self._document_to_cart_item(doc) for doc in docs]
            return cart_items
        except Exception as e:
            raise Exception(f"Error fetching cart for user {user_id}: {str(e)}")

    def update_cart_item(
        self, user_id: str, item_id: str, update_data: CartItemUpdate
    ) -> Optional[CartItem]:
        """
        Update a cart item quantity or price.

        Args:
            user_id (str): The unique identifier of the user
            item_id (str): The unique identifier of the cart item
            update_data (CartItemUpdate): The data to update

        Returns:
            Optional[CartItem]: The updated cart item, or None if item doesn't exist

        Raises:
            Exception: If there's an error updating the item
        """
        try:
            item_ref = (
                self.db.collection(self.CARTS_COLLECTION)
                .document(user_id)
                .collection(self.ITEMS_SUBCOLLECTION)
                .document(item_id)
            )

            # Check if item exists
            if not item_ref.get().exists:
                return None

            # Update only non-None fields
            update_fields = {
                k: v for k, v in update_data.model_dump().items() if v is not None
            }

            item_ref.update(update_fields)

            # Fetch and return the updated item
            return self.get_cart_item(user_id, item_id)
        except Exception as e:
            raise Exception(
                f"Error updating cart item {item_id} for user {user_id}: {str(e)}"
            )

    def remove_item_from_cart(self, user_id: str, item_id: str) -> bool:
        """
        Remove an item from a user's shopping cart.

        Args:
            user_id (str): The unique identifier of the user
            item_id (str): The unique identifier of the cart item to remove

        Returns:
            bool: True if item was deleted, False if item doesn't exist

        Raises:
            Exception: If there's an error removing the item
        """
        try:
            item_ref = (
                self.db.collection(self.CARTS_COLLECTION)
                .document(user_id)
                .collection(self.ITEMS_SUBCOLLECTION)
                .document(item_id)
            )

            # Check if item exists
            if not item_ref.get().exists:
                return False

            item_ref.delete()
            return True
        except Exception as e:
            raise Exception(
                f"Error removing cart item {item_id} for user {user_id}: {str(e)}"
            )

    def clear_user_cart(self, user_id: str) -> int:
        """
        Clear all items from a user's shopping cart.

        Args:
            user_id (str): The unique identifier of the user

        Returns:
            int: Number of items deleted

        Raises:
            Exception: If there's an error clearing the cart
        """
        try:
            items_ref = (
                self.db.collection(self.CARTS_COLLECTION)
                .document(user_id)
                .collection(self.ITEMS_SUBCOLLECTION)
            )

            docs = items_ref.stream()
            deleted_count = 0

            for doc in docs:
                doc.reference.delete()
                deleted_count += 1

            return deleted_count
        except Exception as e:
            raise Exception(f"Error clearing cart for user {user_id}: {str(e)}")

    def get_cart_summary(self, user_id: str) -> dict:
        """
        Get a summary of the user's shopping cart including total price and item count.

        Args:
            user_id (str): The unique identifier of the user

        Returns:
            dict: Dictionary containing:
                - items: List of CartItem objects
                - total_items: Total number of items in cart
                - total_price: Total price of all items
                - item_count: Total quantity of items

        Raises:
            Exception: If there's an error fetching the cart summary
        """
        try:
            cart_items = self.get_user_cart(user_id)

            total_items = len(cart_items)
            total_price = sum(item.price * item.quantity for item in cart_items)
            item_count = sum(item.quantity for item in cart_items)

            return {
                "items": cart_items,
                "total_items": total_items,
                "total_price": round(total_price, 2),
                "item_count": item_count,
            }
        except Exception as e:
            raise Exception(f"Error fetching cart summary for user {user_id}: {str(e)}")

    def update_item_quantity_by_product(
        self, user_id: str, product_id: str, quantity: int
    ) -> Optional[CartItem]:
        """
        Update the quantity of a specific product in the cart.
        If quantity is 0 or less, the item is removed from the cart.

        Args:
            user_id (str): The unique identifier of the user
            product_id (str): The product ID to update (matches cart item ID)
            quantity (int): The new quantity (will remove if <= 0)

        Returns:
            Optional[CartItem]: The updated cart item, or None if removed/not found

        Raises:
            Exception: If there's an error updating the quantity
        """
        try:
            if quantity <= 0:
                # Remove item if quantity is 0 or less
                self.remove_item_from_cart(user_id, product_id)
                return None

            # Update the quantity
            update_data = CartItemUpdate(quantity=quantity)
            return self.update_cart_item(user_id, product_id, update_data)
        except Exception as e:
            raise Exception(
                f"Error updating quantity for product {product_id} in cart: {str(e)}"
            )

    @staticmethod
    def _document_to_cart_item(doc: DocumentSnapshot) -> CartItem:
        """
        Convert a Firestore document snapshot to a CartItem object.

        Args:
            doc (DocumentSnapshot): The Firestore document snapshot

        Returns:
            CartItem: The converted CartItem object
        """
        data = doc.to_dict()
        return CartItem(
            id=doc.id,
            title=data.get("title"),
            author=data.get("author"),
            price=data.get("price"),
            quantity=data.get("quantity"),
            image=data.get("image"),
        )


# Convenience function to create a service instance
def get_cart_service() -> CartService:
    """Create and return a cart service instance."""
    return CartService()
