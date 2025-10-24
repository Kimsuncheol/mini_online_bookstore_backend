# Books API Guide

## Overview

The Books API provides comprehensive endpoints for managing books, categories, and reviews in the BookNest online bookstore. It includes powerful search and filtering capabilities, stock management, and review systems.

## Base URL

```
http://localhost:8000/api/books
```

## Table of Contents

1. [Book CRUD Operations](#book-crud-operations)
2. [Search and Filter](#search-and-filter)
3. [Stock Management](#stock-management)
4. [Category Management](#category-management)
5. [Review Management](#review-management)

---

## Book CRUD Operations

### 1. Create Book

**Endpoint:** `POST /api/books`

**Description:** Create a new book in the bookstore.

**Request Body:**
```json
{
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "isbn": "978-0-7432-7356-5",
  "description": "A classic American novel set in the Jazz Age",
  "genre": "Fiction",
  "language": "English",
  "published_date": "1925-04-10T00:00:00",
  "page_count": 180,
  "price": 12.99,
  "original_price": 15.99,
  "currency": "USD",
  "in_stock": true,
  "stock_quantity": 50,
  "cover_image": "gatsby.jpg",
  "cover_image_url": "https://example.com/images/gatsby.jpg",
  "rating": 4.5,
  "review_count": 0,
  "publisher": "Scribner",
  "edition": "First Edition",
  "is_new": false,
  "is_featured": true,
  "discount": 18.75
}
```

**Response (201 Created):**
```json
{
  "id": "book_12345",
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "isbn": "978-0-7432-7356-5",
  "description": "A classic American novel set in the Jazz Age",
  "genre": "Fiction",
  "language": "English",
  "published_date": "1925-04-10T00:00:00",
  "page_count": 180,
  "price": 12.99,
  "original_price": 15.99,
  "currency": "USD",
  "in_stock": true,
  "stock_quantity": 50,
  "cover_image": "gatsby.jpg",
  "cover_image_url": "https://example.com/images/gatsby.jpg",
  "rating": 4.5,
  "review_count": 0,
  "publisher": "Scribner",
  "edition": "First Edition",
  "created_at": "2025-10-25T10:30:00.000000",
  "updated_at": "2025-10-25T10:30:00.000000",
  "is_new": false,
  "is_featured": true,
  "discount": 18.75
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/books \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "genre": "Fiction",
    "price": 12.99,
    "stock_quantity": 50,
    "in_stock": true
  }'
```

---

### 2. Get Book by ID

**Endpoint:** `GET /api/books/{book_id}`

**Description:** Fetch a specific book by its ID.

**Response (200 OK):**
```json
{
  "id": "book_12345",
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "price": 12.99,
  "genre": "Fiction",
  "in_stock": true,
  "stock_quantity": 50,
  "rating": 4.5,
  "created_at": "2025-10-25T10:30:00.000000",
  "updated_at": "2025-10-25T10:30:00.000000"
}
```

**cURL Example:**
```bash
curl http://localhost:8000/api/books/book_12345
```

---

### 3. Get All Books

**Endpoint:** `GET /api/books`

**Description:** Fetch all books from the bookstore.

**Query Parameters:**
- `limit` (optional): Maximum number of books to return (1-100)

**Response (200 OK):**
```json
[
  {
    "id": "book_12345",
    "title": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "price": 12.99,
    "genre": "Fiction",
    "in_stock": true,
    "stock_quantity": 50
  },
  {
    "id": "book_12346",
    "title": "1984",
    "author": "George Orwell",
    "price": 13.99,
    "genre": "Science Fiction",
    "in_stock": true,
    "stock_quantity": 30
  }
]
```

**cURL Example:**
```bash
curl "http://localhost:8000/api/books?limit=20"
```

---

### 4. Update Book

**Endpoint:** `PATCH /api/books/{book_id}`

**Description:** Update an existing book.

**Request Body (all fields optional):**
```json
{
  "price": 14.99,
  "stock_quantity": 45,
  "rating": 4.7,
  "is_featured": true
}
```

**Response (200 OK):**
```json
{
  "id": "book_12345",
  "title": "The Great Gatsby",
  "price": 14.99,
  "stock_quantity": 45,
  "rating": 4.7,
  "is_featured": true,
  "updated_at": "2025-10-25T11:00:00.000000"
}
```

**cURL Example:**
```bash
curl -X PATCH http://localhost:8000/api/books/book_12345 \
  -H "Content-Type: application/json" \
  -d '{"price": 14.99, "stock_quantity": 45}'
```

---

### 5. Delete Book

**Endpoint:** `DELETE /api/books/{book_id}`

**Description:** Delete a book from the bookstore.

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Book 'book_12345' deleted successfully"
}
```

**cURL Example:**
```bash
curl -X DELETE http://localhost:8000/api/books/book_12345
```

---

## Search and Filter

### 6. Search Books (Advanced)

**Endpoint:** `POST /api/books/search`

**Description:** Search and filter books with advanced criteria and pagination.

**Request Body:**
```json
{
  "genres": ["Fiction", "Science Fiction"],
  "min_price": 10,
  "max_price": 20,
  "rating": 4.0,
  "in_stock_only": true,
  "search_term": "gatsby",
  "sort_by": "price-low-to-high",
  "page": 1,
  "limit": 20
}
```

**Filter Options:**
- `genres`: List of genres to filter by
- `min_price`: Minimum price
- `max_price`: Maximum price
- `rating`: Minimum rating (0-5)
- `in_stock_only`: Show only in-stock books
- `search_term`: Search in title or author
- `sort_by`: Sort order
  - `price-low-to-high`
  - `price-high-to-low`
  - `newest`
  - `rating`
  - `title`
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)

**Response (200 OK):**
```json
{
  "books": [
    {
      "id": "book_12345",
      "title": "The Great Gatsby",
      "author": "F. Scott Fitzgerald",
      "price": 12.99,
      "rating": 4.5,
      "genre": "Fiction",
      "in_stock": true
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 20,
  "total_pages": 1
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/books/search \
  -H "Content-Type: application/json" \
  -d '{
    "genres": ["Fiction"],
    "min_price": 10,
    "max_price": 20,
    "sort_by": "price-low-to-high",
    "page": 1,
    "limit": 20
  }'
```

---

### 7. Get Books by Genre

**Endpoint:** `GET /api/books/genre/{genre}`

**Description:** Fetch books in a specific genre.

**Query Parameters:**
- `limit` (optional): Maximum number of books to return

**Response (200 OK):**
```json
[
  {
    "id": "book_12345",
    "title": "The Great Gatsby",
    "genre": "Fiction",
    "price": 12.99
  }
]
```

**cURL Example:**
```bash
curl "http://localhost:8000/api/books/genre/Fiction?limit=10"
```

---

### 8. Get Featured Books

**Endpoint:** `GET /api/books/featured/list`

**Description:** Fetch featured books.

**Query Parameters:**
- `limit` (optional): Maximum number of books to return (default: 10)

**Response (200 OK):**
```json
[
  {
    "id": "book_12345",
    "title": "The Great Gatsby",
    "is_featured": true,
    "price": 12.99
  }
]
```

**cURL Example:**
```bash
curl "http://localhost:8000/api/books/featured/list?limit=10"
```

---

### 9. Get New Releases

**Endpoint:** `GET /api/books/new-releases/list`

**Description:** Fetch new release books.

**Query Parameters:**
- `limit` (optional): Maximum number of books to return (default: 10)

**Response (200 OK):**
```json
[
  {
    "id": "book_12346",
    "title": "The Midnight Library",
    "is_new": true,
    "price": 16.99
  }
]
```

**cURL Example:**
```bash
curl "http://localhost:8000/api/books/new-releases/list?limit=10"
```

---

## Stock Management

### 10. Update Book Stock

**Endpoint:** `PATCH /api/books/{book_id}/stock`

**Description:** Update book stock quantity (add or reduce inventory).

**Query Parameters:**
- `quantity_change`: Amount to change (positive to add, negative to reduce)

**Response (200 OK):**
```json
{
  "id": "book_12345",
  "title": "The Great Gatsby",
  "stock_quantity": 55,
  "in_stock": true,
  "updated_at": "2025-10-25T12:00:00.000000"
}
```

**Error Response (400 Bad Request):**
```json
{
  "detail": "Cannot reduce stock by 100. Current stock: 50"
}
```

**cURL Examples:**
```bash
# Add 5 books to stock
curl -X PATCH "http://localhost:8000/api/books/book_12345/stock?quantity_change=5"

# Reduce stock by 3 (e.g., after sale)
curl -X PATCH "http://localhost:8000/api/books/book_12345/stock?quantity_change=-3"
```

---

## Category Management

### 11. Create Category

**Endpoint:** `POST /api/books/categories`

**Description:** Create a new book category.

**Request Body:**
```json
{
  "name": "Science Fiction",
  "description": "Futuristic and imaginative stories",
  "icon": "rocket",
  "book_count": 0
}
```

**Response (201 Created):**
```json
{
  "id": "cat_12345",
  "name": "Science Fiction",
  "description": "Futuristic and imaginative stories",
  "icon": "rocket",
  "book_count": 0
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/books/categories \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Science Fiction",
    "description": "Futuristic and imaginative stories",
    "icon": "rocket"
  }'
```

---

### 12. Get All Categories

**Endpoint:** `GET /api/books/categories`

**Description:** Fetch all book categories.

**Response (200 OK):**
```json
[
  {
    "id": "cat_12345",
    "name": "Science Fiction",
    "description": "Futuristic and imaginative stories",
    "icon": "rocket",
    "book_count": 25
  },
  {
    "id": "cat_12346",
    "name": "Fiction",
    "description": "Literary fiction and novels",
    "icon": "book",
    "book_count": 150
  }
]
```

**cURL Example:**
```bash
curl http://localhost:8000/api/books/categories
```

---

### 13. Update Category

**Endpoint:** `PATCH /api/books/categories/{category_id}`

**Description:** Update a book category.

**Request Body:**
```json
{
  "name": "Sci-Fi & Fantasy",
  "book_count": 30
}
```

**Response (200 OK):**
```json
{
  "id": "cat_12345",
  "name": "Sci-Fi & Fantasy",
  "description": "Futuristic and imaginative stories",
  "icon": "rocket",
  "book_count": 30
}
```

**cURL Example:**
```bash
curl -X PATCH http://localhost:8000/api/books/categories/cat_12345 \
  -H "Content-Type: application/json" \
  -d '{"name": "Sci-Fi & Fantasy", "book_count": 30}'
```

---

## Review Management

### 14. Create Review

**Endpoint:** `POST /api/books/reviews`

**Description:** Create a new book review. Automatically updates the book's average rating.

**Request Body:**
```json
{
  "book_id": "book_12345",
  "user_id": "user_123",
  "user_name": "John Doe",
  "rating": 5.0,
  "title": "A Timeless Classic",
  "content": "One of the best books I've ever read. The writing is beautiful and the story is captivating.",
  "helpful": 0
}
```

**Response (201 Created):**
```json
{
  "id": "review_12345",
  "book_id": "book_12345",
  "user_id": "user_123",
  "user_name": "John Doe",
  "rating": 5.0,
  "title": "A Timeless Classic",
  "content": "One of the best books I've ever read. The writing is beautiful and the story is captivating.",
  "helpful": 0,
  "created_at": "2025-10-25T13:00:00.000000",
  "updated_at": "2025-10-25T13:00:00.000000"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/books/reviews \
  -H "Content-Type: application/json" \
  -d '{
    "book_id": "book_12345",
    "user_id": "user_123",
    "user_name": "John Doe",
    "rating": 5.0,
    "title": "A Timeless Classic",
    "content": "One of the best books I have ever read."
  }'
```

---

### 15. Get Book Reviews

**Endpoint:** `GET /api/books/{book_id}/reviews`

**Description:** Fetch all reviews for a specific book.

**Response (200 OK):**
```json
[
  {
    "id": "review_12345",
    "book_id": "book_12345",
    "user_id": "user_123",
    "user_name": "John Doe",
    "rating": 5.0,
    "title": "A Timeless Classic",
    "content": "One of the best books I've ever read.",
    "helpful": 15,
    "created_at": "2025-10-25T13:00:00.000000"
  }
]
```

**cURL Example:**
```bash
curl http://localhost:8000/api/books/book_12345/reviews
```

---

## Database Structure

### Books Collection

```
books (collection)
├── book_12345 (document)
│   ├── title: "The Great Gatsby"
│   ├── author: "F. Scott Fitzgerald"
│   ├── isbn: "978-0-7432-7356-5"
│   ├── genre: "Fiction"
│   ├── price: 12.99
│   ├── stock_quantity: 50
│   ├── in_stock: true
│   ├── rating: 4.5
│   ├── review_count: 10
│   ├── is_featured: true
│   ├── created_at: <timestamp>
│   └── updated_at: <timestamp>
```

### Categories Collection

```
categories (collection)
├── cat_12345 (document)
│   ├── name: "Fiction"
│   ├── description: "Literary fiction and novels"
│   ├── icon: "book"
│   └── book_count: 150
```

### Reviews Collection

```
reviews (collection)
├── review_12345 (document)
│   ├── book_id: "book_12345"
│   ├── user_id: "user_123"
│   ├── user_name: "John Doe"
│   ├── rating: 5.0
│   ├── title: "A Timeless Classic"
│   ├── content: "One of the best books..."
│   ├── helpful: 15
│   ├── created_at: <timestamp>
│   └── updated_at: <timestamp>
```

---

## Validation Rules

| Field | Required | Type | Validation |
|-------|----------|------|------------|
| title | Yes | string | 1-500 chars |
| author | Yes | string | 1-255 chars |
| isbn | No | string | max 20 chars |
| genre | Yes | string | 1-100 chars |
| price | Yes | float | > 0 |
| stock_quantity | Yes | int | >= 0 |
| rating | No | float | 0-5 |
| discount | No | float | 0-100 |
| page_count | No | int | > 0 |

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

## Common Use Cases

### Example 1: Create and Stock a New Book

```bash
# 1. Create the book
curl -X POST http://localhost:8000/api/books \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Midnight Library",
    "author": "Matt Haig",
    "genre": "Fiction",
    "price": 16.99,
    "stock_quantity": 100,
    "in_stock": true,
    "is_new": true,
    "is_featured": true
  }'

# 2. Later, add more stock
curl -X PATCH "http://localhost:8000/api/books/book_12345/stock?quantity_change=50"
```

### Example 2: Search for Books Under $15

```bash
curl -X POST http://localhost:8000/api/books/search \
  -H "Content-Type: application/json" \
  -d '{
    "max_price": 15,
    "in_stock_only": true,
    "sort_by": "price-low-to-high",
    "page": 1,
    "limit": 20
  }'
```

### Example 3: Get Featured Fiction Books

```bash
# First get featured books
curl "http://localhost:8000/api/books/featured/list?limit=20"

# Or search for featured fiction specifically
curl -X POST http://localhost:8000/api/books/search \
  -H "Content-Type: application/json" \
  -d '{
    "genres": ["Fiction"],
    "sort_by": "rating"
  }'
```

---

## Testing with Interactive API Docs

FastAPI provides automatic interactive API documentation. Visit:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

These interfaces allow you to test all endpoints directly from your browser!

---

## Performance Tips

1. **Use Pagination:** Always specify `limit` for large datasets
2. **Filter Early:** Use Firestore queries (genres, in_stock) before Python filtering
3. **Index Fields:** Consider adding Firestore indexes for frequently queried fields
4. **Cache Categories:** Categories change infrequently, consider caching

---

## Future Enhancements

- [ ] Book recommendations based on purchase history
- [ ] Advanced text search with Algolia or Elasticsearch
- [ ] Bulk import/export functionality
- [ ] Book series management
- [ ] Author profiles and pages
- [ ] Wishlist functionality
- [ ] Book availability notifications
- [ ] Related books suggestions
