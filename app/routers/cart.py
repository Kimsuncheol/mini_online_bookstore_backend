"""
Cart Router

Handles shopping cart operations including:
- Adding items to cart
- Viewing cart contents
- Updating item quantities
- Removing items
- Clearing cart
- Getting cart summary
"""

from fastapi import APIRouter, HTTPException, Path, Query
from app.models.cart_item import CartItem, CartItemCreate, CartItemUpdate
from app.services.cart_service import get_cart_service

router = APIRouter(prefix="/api/carts", tags=["cart"])


@router.post("/{user_id}/items")
async def add_item_to_cart(
    user_id: str = Path(..., description="The user ID"),
    item_data: CartItemCreate = None,
):
    """
    Add an item to the user's shopping cart.

    Args:
        user_id (str): The unique identifier of the user
        item_data (CartItemCreate): The cart item data to add

    Returns:
        CartItem: The created cart item with ID

    Raises:
        HTTPException: 400 if invalid data, 500 if database error occurs
    """
    try:
        if not item_data:
            raise HTTPException(status_code=400, detail="Item data is required")

        cart_service = get_cart_service()
        cart_item = cart_service.add_item_to_cart(user_id, item_data)

        return cart_item.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error adding item to cart: {str(e)}",
        )


@router.get("/{user_id}")
async def get_user_cart(user_id: str = Path(..., description="The user ID")):
    """
    Fetch all items from a user's shopping cart.

    Args:
        user_id (str): The unique identifier of the user

    Returns:
        list: List of CartItem objects in the user's cart

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        cart_service = get_cart_service()
        cart_items = cart_service.get_user_cart(user_id)

        return [item.model_dump() for item in cart_items]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching cart: {str(e)}",
        )


@router.get("/{user_id}/items/{item_id}")
async def get_cart_item(
    user_id: str = Path(..., description="The user ID"),
    item_id: str = Path(..., description="The cart item ID"),
):
    """
    Fetch a specific item from a user's shopping cart.

    Args:
        user_id (str): The unique identifier of the user
        item_id (str): The unique identifier of the cart item

    Returns:
        CartItem: The cart item data

    Raises:
        HTTPException: 404 if item not found, 500 if database error occurs
    """
    try:
        cart_service = get_cart_service()
        cart_item = cart_service.get_cart_item(user_id, item_id)

        if cart_item is None:
            raise HTTPException(
                status_code=404,
                detail=f"Cart item '{item_id}' not found for user '{user_id}'",
            )

        return cart_item.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching cart item: {str(e)}",
        )


@router.patch("/{user_id}/items/{item_id}")
async def update_cart_item(
    user_id: str = Path(..., description="The user ID"),
    item_id: str = Path(..., description="The cart item ID"),
    update_data: CartItemUpdate = None,
):
    """
    Update a cart item (quantity or price).

    Args:
        user_id (str): The unique identifier of the user
        item_id (str): The unique identifier of the cart item
        update_data (CartItemUpdate): The data to update

    Returns:
        CartItem: The updated cart item

    Raises:
        HTTPException: 400 if invalid data, 404 if item not found, 500 if database error occurs
    """
    try:
        if not update_data:
            raise HTTPException(status_code=400, detail="Update data is required")

        cart_service = get_cart_service()
        updated_item = cart_service.update_cart_item(user_id, item_id, update_data)

        if updated_item is None:
            raise HTTPException(
                status_code=404,
                detail=f"Cart item '{item_id}' not found for user '{user_id}'",
            )

        return updated_item.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating cart item: {str(e)}",
        )


@router.delete("/{user_id}/items/{item_id}")
async def remove_item_from_cart(
    user_id: str = Path(..., description="The user ID"),
    item_id: str = Path(..., description="The cart item ID"),
):
    """
    Remove an item from a user's shopping cart.

    Args:
        user_id (str): The unique identifier of the user
        item_id (str): The unique identifier of the cart item to remove

    Returns:
        dict: Confirmation message

    Raises:
        HTTPException: 404 if item not found, 500 if database error occurs
    """
    try:
        cart_service = get_cart_service()
        success = cart_service.remove_item_from_cart(user_id, item_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Cart item '{item_id}' not found for user '{user_id}'",
            )

        return {
            "status": "success",
            "message": f"Item '{item_id}' removed from cart",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error removing item from cart: {str(e)}",
        )


@router.delete("/{user_id}")
async def clear_user_cart(user_id: str = Path(..., description="The user ID")):
    """
    Clear all items from a user's shopping cart.

    Args:
        user_id (str): The unique identifier of the user

    Returns:
        dict: Confirmation message with number of items deleted

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        cart_service = get_cart_service()
        deleted_count = cart_service.clear_user_cart(user_id)

        return {
            "status": "success",
            "message": f"Cart cleared for user '{user_id}'",
            "items_deleted": deleted_count,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing cart: {str(e)}",
        )


@router.get("/{user_id}/summary")
async def get_cart_summary(user_id: str = Path(..., description="The user ID")):
    """
    Get a comprehensive summary of the user's shopping cart.

    Includes:
    - All items in the cart
    - Total number of unique items
    - Total price of all items
    - Total quantity of items

    Args:
        user_id (str): The unique identifier of the user

    Returns:
        dict: Cart summary with items, totals, and counts

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        cart_service = get_cart_service()
        summary = cart_service.get_cart_summary(user_id)

        # Convert CartItem objects to dictionaries
        return {
            "user_id": user_id,
            "items": [item.model_dump() for item in summary["items"]],
            "total_items": summary["total_items"],
            "total_price": summary["total_price"],
            "item_count": summary["item_count"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching cart summary: {str(e)}",
        )


@router.patch("/{user_id}/items/{product_id}/quantity")
async def update_item_quantity(
    user_id: str = Path(..., description="The user ID"),
    product_id: str = Path(..., description="The product ID"),
    quantity: int = Query(..., gt=0, description="The new quantity (must be greater than 0)"),
):
    """
    Update the quantity of a specific product in the cart.

    Args:
        user_id (str): The unique identifier of the user
        product_id (str): The product ID to update
        quantity (int): The new quantity (must be greater than 0)

    Returns:
        CartItem: The updated cart item

    Raises:
        HTTPException: 400 if quantity invalid, 404 if item not found, 500 if database error occurs
    """
    try:
        if quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="Quantity must be greater than 0. Use DELETE to remove the item.",
            )

        cart_service = get_cart_service()
        updated_item = cart_service.update_item_quantity_by_product(
            user_id, product_id, quantity
        )

        if updated_item is None:
            raise HTTPException(
                status_code=404,
                detail=f"Product '{product_id}' not found in cart for user '{user_id}'",
            )

        return updated_item.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating quantity: {str(e)}",
        )
