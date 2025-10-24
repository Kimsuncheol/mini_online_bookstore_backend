# Shopping Cart API Guide

## Overview

The Cart API provides endpoints for managing user shopping carts with the following operations:
- Add items to cart
- View cart contents
- Update item quantities
- Remove items
- Clear entire cart
- Get cart summary with totals

## Base URL

```
http://localhost:8000/api/carts
```

## API Endpoints

### 1. Add Item to Cart

**Endpoint:** `POST /api/carts/{user_id}/items`

**Description:** Add a new item to the user's shopping cart.

**Parameters:**
- `user_id` (path, required): The unique identifier of the user

**Request Body:**
```json
{
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "price": 12.99,
  "quantity": 1,
  "image": "https://example.com/gatsby.jpg"
}
```

**Response (201 Created):**
```json
{
  "id": "item_12345",
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "price": 12.99,
  "quantity": 1,
  "image": "https://example.com/gatsby.jpg"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/carts/user123/items \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "price": 12.99,
    "quantity": 1,
    "image": "https://example.com/gatsby.jpg"
  }'
```

---

### 2. Get User Cart

**Endpoint:** `GET /api/carts/{user_id}`

**Description:** Fetch all items from a user's shopping cart.

**Parameters:**
- `user_id` (path, required): The unique identifier of the user

**Response (200 OK):**
```json
[
  {
    "id": "item_12345",
    "title": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "price": 12.99,
    "quantity": 1,
    "image": "https://example.com/gatsby.jpg"
  },
  {
    "id": "item_12346",
    "title": "To Kill a Mockingbird",
    "author": "Harper Lee",
    "price": 14.99,
    "quantity": 2,
    "image": "https://example.com/mockingbird.jpg"
  }
]
```

**cURL Example:**
```bash
curl http://localhost:8000/api/carts/user123
```

---

### 3. Get Specific Cart Item

**Endpoint:** `GET /api/carts/{user_id}/items/{item_id}`

**Description:** Fetch a specific item from a user's shopping cart.

**Parameters:**
- `user_id` (path, required): The unique identifier of the user
- `item_id` (path, required): The unique identifier of the cart item

**Response (200 OK):**
```json
{
  "id": "item_12345",
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "price": 12.99,
  "quantity": 1,
  "image": "https://example.com/gatsby.jpg"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Cart item 'item_12345' not found for user 'user123'"
}
```

**cURL Example:**
```bash
curl http://localhost:8000/api/carts/user123/items/item_12345
```

---

### 4. Update Cart Item

**Endpoint:** `PATCH /api/carts/{user_id}/items/{item_id}`

**Description:** Update a cart item's quantity or price.

**Parameters:**
- `user_id` (path, required): The unique identifier of the user
- `item_id` (path, required): The unique identifier of the cart item

**Request Body:**
```json
{
  "quantity": 3,
  "price": 12.99
}
```

**Response (200 OK):**
```json
{
  "id": "item_12345",
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "price": 12.99,
  "quantity": 3,
  "image": "https://example.com/gatsby.jpg"
}
```

**cURL Example:**
```bash
curl -X PATCH http://localhost:8000/api/carts/user123/items/item_12345 \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 3
  }'
```

---

### 5. Update Item Quantity

**Endpoint:** `PATCH /api/carts/{user_id}/items/{product_id}/quantity`

**Description:** Update the quantity of a specific product in the cart using a query parameter.

**Parameters:**
- `user_id` (path, required): The unique identifier of the user
- `product_id` (path, required): The product ID to update
- `quantity` (query, required): The new quantity (must be > 0)

**Response (200 OK):**
```json
{
  "id": "item_12345",
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "price": 12.99,
  "quantity": 5,
  "image": "https://example.com/gatsby.jpg"
}
```

**cURL Example:**
```bash
curl -X PATCH "http://localhost:8000/api/carts/user123/items/product_12345/quantity?quantity=5"
```

---

### 6. Remove Item from Cart

**Endpoint:** `DELETE /api/carts/{user_id}/items/{item_id}`

**Description:** Remove an item from a user's shopping cart.

**Parameters:**
- `user_id` (path, required): The unique identifier of the user
- `item_id` (path, required): The unique identifier of the cart item to remove

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Item 'item_12345' removed from cart"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Cart item 'item_12345' not found for user 'user123'"
}
```

**cURL Example:**
```bash
curl -X DELETE http://localhost:8000/api/carts/user123/items/item_12345
```

---

### 7. Clear User Cart

**Endpoint:** `DELETE /api/carts/{user_id}`

**Description:** Clear all items from a user's shopping cart.

**Parameters:**
- `user_id` (path, required): The unique identifier of the user

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Cart cleared for user 'user123'",
  "items_deleted": 5
}
```

**cURL Example:**
```bash
curl -X DELETE http://localhost:8000/api/carts/user123
```

---

### 8. Get Cart Summary

**Endpoint:** `GET /api/carts/{user_id}/summary`

**Description:** Get a comprehensive summary of the user's shopping cart including totals.

**Parameters:**
- `user_id` (path, required): The unique identifier of the user

**Response (200 OK):**
```json
{
  "user_id": "user123",
  "items": [
    {
      "id": "item_12345",
      "title": "The Great Gatsby",
      "author": "F. Scott Fitzgerald",
      "price": 12.99,
      "quantity": 2,
      "image": "https://example.com/gatsby.jpg"
    },
    {
      "id": "item_12346",
      "title": "To Kill a Mockingbird",
      "author": "Harper Lee",
      "price": 14.99,
      "quantity": 1,
      "image": "https://example.com/mockingbird.jpg"
    }
  ],
  "total_items": 2,
  "total_price": 40.97,
  "item_count": 3
}
```

**Breakdown:**
- `total_items`: Number of unique items in cart (2)
- `item_count`: Total quantity of all items (2 + 1 = 3)
- `total_price`: Sum of (price × quantity) for all items

**cURL Example:**
```bash
curl http://localhost:8000/api/carts/user123/summary
```

---

## Database Structure

The cart data is stored in Firestore with the following structure:

```
carts (collection)
└── {userId} (document)
    └── items (subcollection)
        ├── item_12345 (document)
        │   ├── title: "The Great Gatsby"
        │   ├── author: "F. Scott Fitzgerald"
        │   ├── price: 12.99
        │   ├── quantity: 2
        │   └── image: "https://example.com/gatsby.jpg"
        │
        └── item_12346 (document)
            ├── title: "To Kill a Mockingbird"
            ├── author: "Harper Lee"
            ├── price: 14.99
            ├── quantity: 1
            └── image: "https://example.com/mockingbird.jpg"
```

---

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "detail": "Item data is required"
}
```

**404 Not Found:**
```json
{
  "detail": "Cart item 'item_12345' not found for user 'user123'"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Error adding item to cart: {error_message}"
}
```

---

## Examples

### Complete Workflow

**1. Add multiple items to cart:**
```bash
curl -X POST http://localhost:8000/api/carts/user123/items \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "price": 12.99,
    "quantity": 1
  }'

curl -X POST http://localhost:8000/api/carts/user123/items \
  -H "Content-Type: application/json" \
  -d '{
    "title": "1984",
    "author": "George Orwell",
    "price": 13.99,
    "quantity": 2
  }'
```

**2. View cart:**
```bash
curl http://localhost:8000/api/carts/user123
```

**3. Get cart summary:**
```bash
curl http://localhost:8000/api/carts/user123/summary
```

**4. Update item quantity:**
```bash
curl -X PATCH "http://localhost:8000/api/carts/user123/items/item_12345/quantity?quantity=3"
```

**5. Remove an item:**
```bash
curl -X DELETE http://localhost:8000/api/carts/user123/items/item_12345
```

**6. Clear entire cart:**
```bash
curl -X DELETE http://localhost:8000/api/carts/user123
```

---

## Validation Rules

| Field | Rule | Example |
|-------|------|---------|
| `title` | Required, max 255 chars | "The Great Gatsby" |
| `author` | Required, max 255 chars | "F. Scott Fitzgerald" |
| `price` | Required, must be > 0 | 12.99 |
| `quantity` | Required, must be > 0 | 1 |
| `image` | Optional | "https://example.com/image.jpg" |

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request succeeded |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Invalid input data |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error - Server error occurred |

---

## Testing with Postman

You can easily test these endpoints using Postman:

1. **Create Collection:** "Mini Bookstore - Cart API"
2. **Create Requests:**
   - POST `/api/carts/{user_id}/items` - Add item
   - GET `/api/carts/{user_id}` - View cart
   - GET `/api/carts/{user_id}/items/{item_id}` - Get item
   - PATCH `/api/carts/{user_id}/items/{item_id}` - Update item
   - DELETE `/api/carts/{user_id}/items/{item_id}` - Remove item
   - DELETE `/api/carts/{user_id}` - Clear cart
   - GET `/api/carts/{user_id}/summary` - Get summary

3. **Set Environment Variable:** `user_id=user123`

---

## Performance Considerations

- **Cart Summary:** Calculates totals in real-time from Firestore
- **Subcollection Queries:** Items are stored as subcollections for easy per-user isolation
- **Indexing:** Consider adding Firestore indexes for large-scale deployments

---

## Future Enhancements

- [ ] Cart item discounts/coupons
- [ ] Persistent cart (recovery for abandoned carts)
- [ ] Cart item notes/preferences
- [ ] Bulk operations (add multiple items at once)
- [ ] Cart expiration (auto-clear after X days)
- [ ] Save for later feature
