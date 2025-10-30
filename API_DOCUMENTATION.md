# Search API Documentation

Complete API reference for the search functionality integrated in the Mini Online Bookstore Backend.

**Base URL**: `http://localhost:8000/search`

---

## Table of Contents

1. [POST /search](#post-search) - Perform book search
2. [GET /search/history/{user_id}](#get-searchhistoryuser_id) - Get search history
3. [DELETE /search/history/{user_id}](#delete-searchhistoryuser_id) - Clear search history
4. [GET /search/popular](#get-searchpopular) - Get popular searches
5. [GET /search/suggestions/related/{book_id}](#get-searchsuggestions-relatedbook_id) - Related searches
6. [POST /search/expand](#post-searchexpand) - Expand query
7. [POST /search/analyze-similarity](#post-searchanalyze-similarity) - Find similar books

---

## POST /search

Perform a comprehensive book search with fuzzy matching and AI suggestions.

### Request

**Method**: `POST`

**URL**: `/search`

**Content-Type**: `application/json`

### Request Body

```typescript
{
  // Required
  query: string                    // Search query (1-500 characters)

  // Optional
  search_type?: "all" | "books" | "authors" | "categories"  // Default: "all"

  filters?: {
    genres?: string[]              // Filter by genres
    min_price?: number              // Minimum price (>=0)
    max_price?: number              // Maximum price (>0)
    rating?: number                 // Minimum rating (0-5)
    in_stock_only?: boolean         // Only in-stock books
  }

  settings?: {
    history_enabled?: boolean       // Save search history (default: true)
    fuzzy_matching?: boolean        // Use fuzzy matching (default: true)
    include_suggestions?: boolean   // Include AI suggestions (default: true)
    fuzzy_threshold?: number        // Similarity threshold 0-1 (default: 0.6)
    max_suggestions?: number        // Max suggestions 1-20 (default: 5)
  }

  page?: number                    // Page number (default: 1, min: 1)
  page_size?: number               // Results per page (default: 20, min: 1, max: 100)
  user_id?: string                 // User ID for personalization
}
```

### Response

**Status**: `200 OK`

```typescript
{
  success: boolean
  results: SearchResult[]
  total_count: number
  suggested_keywords?: string[]
  processing_time_ms: number
  page: number
  page_size: number
  has_more: boolean
  error?: string                   // Only if success is false
}
```

### SearchResult Object

```typescript
{
  id: string
  title: string
  type: "book" | "author" | "category"
  subtitle?: string
  image_url?: string
  url: string
  relevance_score?: number         // 0-1
  description?: string
  metadata?: {
    author?: string
    genre?: string
    price?: number
    rating?: number
    in_stock?: boolean
    [key: string]: any
  }
}
```

### Example Request

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "harry potter",
    "search_type": "books",
    "filters": {
      "genres": ["Fantasy"],
      "min_price": 5.0,
      "max_price": 30.0
    },
    "settings": {
      "history_enabled": true,
      "fuzzy_matching": true,
      "include_suggestions": true,
      "fuzzy_threshold": 0.6,
      "max_suggestions": 5
    },
    "page": 1,
    "page_size": 20,
    "user_id": "user_123"
  }'
```

### Example Response

```json
{
  "success": true,
  "results": [
    {
      "id": "book_1",
      "title": "Harry Potter and the Philosopher's Stone",
      "type": "book",
      "subtitle": "by J.K. Rowling",
      "image_url": "https://example.com/cover.jpg",
      "url": "/books/book_1",
      "relevance_score": 0.98,
      "description": "A young wizard discovers...",
      "metadata": {
        "author": "J.K. Rowling",
        "genre": "Fantasy",
        "price": 12.99,
        "rating": 4.8,
        "in_stock": true
      }
    }
  ],
  "total_count": 7,
  "suggested_keywords": [
    "wizard novels",
    "magical schools",
    "fantasy adventure",
    "young adult magic"
  ],
  "processing_time_ms": 234,
  "page": 1,
  "page_size": 20,
  "has_more": false
}
```

### Error Handling

- `400`: Empty query
- `500`: Server error

---

## GET /search/history/{user_id}

Retrieve search history for a user.

### Request

**Method**: `GET`

**URL**: `/search/history/{user_id}`

### Query Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `limit` | integer | 20 | 100 | Max items to return |

### Response

```typescript
SearchHistoryItem[]

interface SearchHistoryItem {
  id: string
  query: string
  timestamp: datetime
  user_id: string
  result_count: number
  search_type: "all" | "books" | "authors" | "categories"
}
```

### Example Request

```bash
curl "http://localhost:8000/search/history/user_123?limit=10"
```

### Example Response

```json
[
  {
    "id": "history_1",
    "query": "fantasy novels",
    "timestamp": "2024-01-15T10:30:00",
    "user_id": "user_123",
    "result_count": 45,
    "search_type": "books"
  },
  {
    "id": "history_2",
    "query": "harry potter",
    "timestamp": "2024-01-15T09:15:00",
    "user_id": "user_123",
    "result_count": 7,
    "search_type": "books"
  }
]
```

---

## DELETE /search/history/{user_id}

Clear all search history for a user.

### Request

**Method**: `DELETE`

**URL**: `/search/history/{user_id}`

### Response

```json
{
  "message": "Search history cleared successfully"
}
```

### Example Request

```bash
curl -X DELETE "http://localhost:8000/search/history/user_123"
```

---

## GET /search/popular

Get the most popular/trending search queries across all users.

### Request

**Method**: `GET`

**URL**: `/search/popular`

### Query Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `limit` | integer | 10 | 50 | Max searches to return |

### Response

```typescript
{
  popular_searches: Array<{
    query: string
    count: number
  }>
  total: number
}
```

### Example Request

```bash
curl "http://localhost:8000/search/popular?limit=10"
```

### Example Response

```json
{
  "popular_searches": [
    {
      "query": "fantasy",
      "count": 523
    },
    {
      "query": "harry potter",
      "count": 412
    },
    {
      "query": "romance novels",
      "count": 387
    }
  ],
  "total": 3
}
```

---

## GET /search/suggestions/related/{book_id}

Get AI-powered search suggestions related to a specific book.

### Request

**Method**: `GET`

**URL**: `/search/suggestions/related/{book_id}`

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `book_id` | string | ID of the book |

### Response

```typescript
{
  book_id: string
  book_title: string
  related_searches: Array<{
    keyword: string
    description: string
  }>
}
```

### Example Request

```bash
curl "http://localhost:8000/search/suggestions/related/book_123"
```

### Example Response

```json
{
  "book_id": "book_123",
  "book_title": "Harry Potter and the Philosopher's Stone",
  "related_searches": [
    {
      "keyword": "wizard school",
      "description": "Similar magical education setting"
    },
    {
      "keyword": "boarding school adventure",
      "description": "Young characters in a school environment"
    },
    {
      "keyword": "chosen one fantasy",
      "description": "Hero's journey and destiny themes"
    },
    {
      "keyword": "magical creatures",
      "description": "Fantasy world with magical beings"
    },
    {
      "keyword": "coming of age magic",
      "description": "Young protagonist discovering powers"
    }
  ]
}
```

---

## POST /search/expand

Expand a search query with synonyms, related terms, and variations.

### Request

**Method**: `POST`

**URL**: `/search/expand`

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Query to expand (required) |

### Response

```typescript
{
  original_query: string
  expanded_terms: {
    synonyms: string[]
    related: string[]
    broader: string[]
    narrower: string[]
  }
}
```

### Example Request

```bash
curl -X POST "http://localhost:8000/search/expand?query=dragon"
```

### Example Response

```json
{
  "original_query": "dragon",
  "expanded_terms": {
    "synonyms": ["drake", "wyrm", "flying reptile"],
    "related": ["fantasy", "adventure", "treasure", "magic"],
    "broader": ["mythical creature", "fantasy being"],
    "narrower": ["fire dragon", "ice dragon", "ancient dragon"]
  }
}
```

---

## POST /search/analyze-similarity

Find books semantically similar to a search query using AI analysis.

### Request

**Method**: `POST`

**URL**: `/search/analyze-similarity`

### Query Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `query` | string | - | - | Search query (required) |
| `limit` | integer | 5 | 20 | Max results to return |

### Response

```typescript
{
  query: string
  similar_books: Array<{
    book_id: string
    title: string
    similarity_score: number  // 0-1
  }>
  count: number
}
```

### Example Request

```bash
curl -X POST "http://localhost:8000/search/analyze-similarity?query=coming%20of%20age%20magic&limit=5"
```

### Example Response

```json
{
  "query": "coming of age magic",
  "similar_books": [
    {
      "book_id": "book_1",
      "title": "Harry Potter and the Philosopher's Stone",
      "similarity_score": 0.92
    },
    {
      "book_id": "book_2",
      "title": "Percy Jackson and the Olympians",
      "similarity_score": 0.88
    },
    {
      "book_id": "book_3",
      "title": "The Cruel Prince",
      "similarity_score": 0.85
    },
    {
      "book_id": "book_4",
      "title": "A Darker Shade of Magic",
      "similarity_score": 0.82
    },
    {
      "book_id": "book_5",
      "title": "Six of Crows",
      "similarity_score": 0.79
    }
  ],
  "count": 5
}
```

---

## Error Responses

All endpoints may return error responses with the following format:

```json
{
  "detail": "Error message describing the issue"
}
```

### Common Error Codes

| Code | Scenario |
|------|----------|
| 400 | Invalid request parameters (e.g., empty query) |
| 404 | Resource not found (e.g., book not found) |
| 500 | Server error (e.g., database connection failure) |

---

## Rate Limiting

No explicit rate limiting is currently implemented. For production, consider adding:

- IP-based rate limiting (e.g., 100 requests/minute)
- User-based rate limiting (e.g., 1000 requests/day)
- Endpoint-specific limits for expensive operations

---

## Best Practices

### 1. Search Queries
- Keep queries concise (1-50 characters optimal)
- Use natural language
- Include keywords for better results

### 2. Filters
- Use filters to narrow results (faster queries)
- Combine multiple filters for better results
- Price ranges should be realistic

### 3. Pagination
- Use reasonable page sizes (10-50 recommended)
- Check `has_more` to determine if more results exist
- Don't request excessive pages at once

### 4. AI Features
- Enable suggestions only when needed (adds ~500-2000ms)
- Cache results when possible
- Use `expand` before main search for better queries

### 5. History Management
- Regularly clean up user history (optional)
- Don't store sensitive information in queries
- Monitor analytics for popular searches

---

## Performance Tips

1. **Use Fuzzy Matching**: Enables typo tolerance (small performance cost)
2. **Set Appropriate Thresholds**: Higher threshold = faster, fewer results
3. **Enable Caching**: AI suggestions are cached 24 hours
4. **Batch Operations**: Don't make sequential searches in a loop
5. **Use Filters**: Reduces data processing significantly

---

## Testing with cURL

### Basic Search
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"fantasy"}'
```

### Search with Filters
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "fantasy",
    "filters": {
      "min_price": 10,
      "max_price": 50,
      "in_stock_only": true
    }
  }'
```

### Get Search History
```bash
curl "http://localhost:8000/search/history/user_123?limit=20"
```

### Get Popular Searches
```bash
curl "http://localhost:8000/search/popular?limit=10"
```

### Expand Query
```bash
curl -X POST "http://localhost:8000/search/expand?query=wizard"
```

---

## Integration Examples

### Python Requests
```python
import requests

# Search
response = requests.post(
    "http://localhost:8000/search",
    json={
        "query": "harry potter",
        "search_type": "books",
        "page": 1,
        "page_size": 20
    }
)
results = response.json()
print(f"Found {results['total_count']} books")

# Get history
history = requests.get(
    "http://localhost:8000/search/history/user_123",
    params={"limit": 10}
).json()
```

### JavaScript/Fetch
```javascript
// Search
const response = await fetch("http://localhost:8000/search", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    query: "fantasy",
    search_type: "books",
    page: 1,
    page_size: 20
  })
});
const results = await response.json();
console.log(`Found ${results.total_count} results`);
```

---

## OpenAPI Documentation

Interactive API documentation available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Support & Questions

For implementation details, see:
- `SEARCH_IMPLEMENTATION.md` - Technical guide
- `SEARCH_USAGE_EXAMPLES.md` - Code examples
- `INTEGRATION_CHECKLIST.md` - Integration guide

For issues with specific endpoints, check the endpoint documentation above and ensure:
1. All required parameters are provided
2. Parameter types match specifications
3. Query strings are properly URL-encoded
4. Firebase/OpenAI APIs are accessible
