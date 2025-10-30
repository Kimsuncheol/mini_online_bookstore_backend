# Search Implementation - Usage Examples

Practical examples for using the search functionality implemented in Missions 1-3.

---

## Table of Contents
1. [N-gram Utilities](#n-gram-utilities)
2. [Search Service](#search-service)
3. [Search Suggestions](#search-suggestions)
4. [API Endpoints](#api-endpoints)
5. [Integration Examples](#integration-examples)

---

## N-gram Utilities

### Import
```python
from app.utils.ngram import (
    generate_character_ngrams,
    generate_word_ngrams,
    calculate_string_similarity,
    find_similar_strings,
    build_search_index,
    search_using_index,
)
```

### Example 1: Fuzzy Matching for Typo Tolerance

```python
# User types "harey potter" instead of "harry potter"
query = "harey potter"
books = ["Harry Potter", "Percy Jackson", "The Hobbit"]

# Find similar books despite typo
results = find_similar_strings(
    query=query,
    candidates=books,
    threshold=0.5,
    ngram_type="char",
    n=3
)

for book, score in results:
    print(f"{book}: {score:.2%} match")

# Output:
# Harry Potter: 89% match
```

### Example 2: Word-level N-gram Matching

```python
# User searches for "fantasy novels about magic"
query = "fantasy novels about magic"

# Generate word n-grams (bigrams)
query_ngrams = generate_word_ngrams(query, n=2)
print(query_ngrams)
# Output: {'fantasy novels', 'novels about', 'about magic'}

# Compare with book descriptions
book_desc = "Magic is central to this fantasy novel about adventure"
book_ngrams = generate_word_ngrams(book_desc, n=2)

# Calculate similarity
similarity = calculate_string_similarity(
    query,
    book_desc,
    ngram_type="word",
    n=2
)
print(f"Similarity: {similarity:.2%}")
# Output: Similarity: 78.50%
```

### Example 3: Building a Search Index

```python
# Index a collection of book titles for fast searching
books_list = [
    "The Great Gatsby",
    "The Catcher in the Rye",
    "The Hobbit",
    "Harry Potter",
    "Percy Jackson",
]

# Build index once
index = build_search_index(books_list, ngram_type="char", n=3)

# Now perform multiple searches efficiently
queries = ["gatsby", "catcher", "hobbit", "harry"]

for q in queries:
    results = search_using_index(q, index, books_list)
    if results:
        print(f"'{q}' -> {results[0][0]} ({results[0][1]:.2%})")

# Output:
# 'gatsby' -> The Great Gatsby (93%)
# 'catcher' -> The Catcher in the Rye (91%)
# 'hobbit' -> The Hobbit (95%)
# 'harry' -> Harry Potter (92%)
```

---

## Search Service

### Import
```python
from app.services.search_service import get_search_service
from app.models.search import SearchRequest, SearchSettings
```

### Example 1: Basic Book Search

```python
async def basic_search():
    search_service = get_search_service()

    request = SearchRequest(
        query="fantasy novels",
        search_type="books",
        page=1,
        page_size=10
    )

    response = await search_service.search(request)

    print(f"Found {response.total_count} results")
    for result in response.results:
        print(f"- {result.title} ({result.relevance_score:.0%} match)")
        print(f"  {result.description[:100]}...")
```

### Example 2: Search with Filters

```python
async def filtered_search():
    search_service = get_search_service()

    request = SearchRequest(
        query="magic",
        search_type="books",
        filters={
            "genres": ["Fantasy", "Young Adult"],
            "min_price": 10.0,
            "max_price": 30.0,
            "rating": 4.0,
            "in_stock_only": True
        },
        page=1,
        page_size=20
    )

    response = await search_service.search(request)

    print(f"Filtered results: {response.total_count}")
    for result in response.results:
        metadata = result.metadata or {}
        print(f"- {result.title}")
        print(f"  Genre: {metadata.get('genre')}")
        print(f"  Price: ${metadata.get('price')}")
        print(f"  Rating: {metadata.get('rating')}/5")
```

### Example 3: Search with AI Suggestions

```python
async def search_with_suggestions():
    search_service = get_search_service()

    request = SearchRequest(
        query="wizard",
        search_type="books",
        settings=SearchSettings(
            history_enabled=True,
            fuzzy_matching=True,
            include_suggestions=True,  # Enable AI suggestions
            fuzzy_threshold=0.6,
            max_suggestions=5
        ),
        page=1,
        page_size=20,
        user_id="user_123"
    )

    response = await search_service.search(request)

    print(f"Results: {response.total_count}")
    print("\nTop results:")
    for result in response.results[:5]:
        print(f"- {result.title}")

    print("\nAI Suggestions:")
    if response.suggested_keywords:
        for keyword in response.suggested_keywords:
            print(f"- {keyword}")
```

### Example 4: Search History

```python
def manage_search_history():
    search_service = get_search_service()
    user_id = "user_123"

    # Get search history
    history = search_service.get_search_history(user_id, limit=20)

    print("Recent searches:")
    for item in history:
        print(f"- '{item.query}' ({item.result_count} results)")
        print(f"  {item.timestamp}")

    # Clear history
    success = search_service.clear_search_history(user_id)
    if success:
        print("History cleared!")
```

### Example 5: Popular Searches

```python
def get_trending_searches():
    search_service = get_search_service()

    popular = search_service.get_popular_searches(limit=10)

    print("Trending searches:")
    for search in popular:
        print(f"- '{search['query']}' ({search['count']} searches)")
```

---

## Search Suggestions

### Import
```python
from app.services.search_suggestion_service import get_search_suggestion_service
```

### Example 1: Generate Keyword Suggestions

```python
async def get_search_suggestions():
    suggestion_service = get_search_suggestion_service()

    query = "fantasy adventure"
    results = [...]  # List of SearchResult objects

    suggestions = await suggestion_service.generate_search_suggestions(
        query=query,
        results=results,
        max_suggestions=5,
        use_cache=True
    )

    print(f"Suggestions for '{query}':")
    for suggestion in suggestions:
        print(f"- {suggestion}")

    # Output:
    # Suggestions for 'fantasy adventure':
    # - wizard quest
    # - epic fantasy
    # - magical journey
    # - sword and sorcery
    # - high fantasy adventure
```

### Example 2: Content-based Similarity Analysis

```python
async def analyze_similar_books():
    from app.services.book_service import get_book_service

    suggestion_service = get_search_suggestion_service()
    book_service = get_book_service()

    # Get all books
    all_books = book_service.get_all_books(limit=50)

    # Find books similar to a query
    query = "coming of age magical school"
    similar = await suggestion_service.analyze_content_similarity(
        query=query,
        books=all_books,
        top_k=5
    )

    print(f"Books similar to '{query}':")
    for result in similar:
        print(f"- {result['title']}: {result['similarity_score']:.0%} match")

    # Output:
    # Books similar to 'coming of age magical school':
    # - Harry Potter: 92% match
    # - Percy Jackson: 88% match
    # - The Cruel Prince: 85% match
```

### Example 3: Get Related Searches for a Book

```python
async def get_book_related_searches():
    from app.services.book_service import get_book_service

    suggestion_service = get_search_suggestion_service()
    book_service = get_book_service()

    # Get a specific book
    book = book_service.get_book_by_id("book_123")

    # Get related search suggestions
    related = await suggestion_service.get_related_searches(
        book=book,
        max_suggestions=5
    )

    print(f"Related searches for '{book.title}':")
    for item in related:
        print(f"- {item['keyword']}")
        print(f"  {item['description']}")

    # Output:
    # Related searches for 'Harry Potter':
    # - wizard school
    #   Similar magical education setting
    # - boarding school adventure
    #   Young characters in a school environment
    # - chosen one fantasy
    #   Hero's journey and destiny themes
```

### Example 4: Query Expansion

```python
async def expand_search_query():
    suggestion_service = get_search_suggestion_service()

    query = "dragon"

    expanded = await suggestion_service.expand_query(
        query=query,
        max_terms=5
    )

    print(f"Query: '{query}'")
    print("\nSynonyms:")
    for term in expanded["synonyms"]:
        print(f"- {term}")

    print("\nRelated terms:")
    for term in expanded["related"]:
        print(f"- {term}")

    print("\nBroader terms:")
    for term in expanded["broader"]:
        print(f"- {term}")

    print("\nNarrower terms:")
    for term in expanded["narrower"]:
        print(f"- {term}")

    # Output:
    # Query: 'dragon'
    #
    # Synonyms:
    # - drake
    # - wyrm
    # - flying reptile
    #
    # Related terms:
    # - fantasy
    # - adventure
    # - treasure
    #
    # Broader terms:
    # - mythical creature
    # - fantasy being
    #
    # Narrower terms:
    # - fire dragon
    # - ice dragon
```

---

## API Endpoints

### Example 1: POST /search

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "harry potter",
    "search_type": "books",
    "filters": {
      "genres": ["Fantasy"],
      "min_price": 5.0
    },
    "settings": {
      "history_enabled": true,
      "fuzzy_matching": true,
      "include_suggestions": true
    },
    "page": 1,
    "page_size": 20,
    "user_id": "user_123"
  }'
```

Response:
```json
{
  "success": true,
  "results": [
    {
      "id": "book_1",
      "title": "Harry Potter and the Philosopher's Stone",
      "type": "book",
      "subtitle": "by J.K. Rowling",
      "image_url": "https://...",
      "url": "/books/book_1",
      "relevance_score": 0.98,
      "metadata": {
        "author": "J.K. Rowling",
        "genre": "Fantasy",
        "price": 12.99,
        "rating": 4.8
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

### Example 2: GET /search/history/{user_id}

```bash
curl "http://localhost:8000/search/history/user_123?limit=10"
```

Response:
```json
[
  {
    "id": "history_456",
    "query": "fantasy novels",
    "timestamp": "2024-01-15T10:30:00",
    "user_id": "user_123",
    "result_count": 45,
    "search_type": "books"
  },
  {
    "id": "history_457",
    "query": "harry potter",
    "timestamp": "2024-01-15T09:15:00",
    "user_id": "user_123",
    "result_count": 7,
    "search_type": "books"
  }
]
```

### Example 3: GET /search/suggestions/related/{book_id}

```bash
curl "http://localhost:8000/search/suggestions/related/book_123"
```

Response:
```json
{
  "book_id": "book_123",
  "book_title": "Harry Potter and the Philosopher's Stone",
  "related_searches": [
    {
      "keyword": "wizard school fantasy",
      "description": "Books featuring magical education settings"
    },
    {
      "keyword": "coming of age magic",
      "description": "Young characters discovering magical powers"
    },
    {
      "keyword": "boarding school adventure",
      "description": "Adventure in residential school settings"
    }
  ]
}
```

### Example 4: POST /search/expand

```bash
curl -X POST "http://localhost:8000/search/expand?query=magic"
```

Response:
```json
{
  "original_query": "magic",
  "expanded_terms": {
    "synonyms": ["sorcery", "witchcraft", "spellcasting"],
    "related": ["fantasy", "supernatural", "mystery"],
    "broader": ["supernatural phenomena"],
    "narrower": ["spell", "potion", "enchantment"]
  }
}
```

---

## Integration Examples

### Example 1: Search in FastAPI Route

```python
from fastapi import FastAPI, HTTPException
from app.models.search import SearchRequest
from app.services.search_service import get_search_service

app = FastAPI()
search_service = get_search_service()

@app.post("/api/search")
async def search_books(request: SearchRequest):
    try:
        response = await search_service.search(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Example 2: Advanced Search Component

```python
from app.services.search_service import get_search_service
from app.services.search_suggestion_service import get_search_suggestion_service
from app.models.search import SearchRequest, SearchSettings

class AdvancedSearchComponent:
    def __init__(self):
        self.search_service = get_search_service()
        self.suggestion_service = get_search_suggestion_service()

    async def perform_advanced_search(
        self,
        query: str,
        user_id: str,
        filters: dict = None,
    ):
        """
        Perform advanced search with all features enabled.
        """
        # Create request with all features
        request = SearchRequest(
            query=query,
            search_type="books",
            filters=filters,
            settings=SearchSettings(
                history_enabled=True,
                fuzzy_matching=True,
                include_suggestions=True,
                fuzzy_threshold=0.6,
                max_suggestions=5
            ),
            page=1,
            page_size=20,
            user_id=user_id
        )

        # Perform search
        response = await self.search_service.search(request)

        # Optionally, expand the query for user awareness
        if response.results:
            expanded = await self.suggestion_service.expand_query(query)
            response.suggested_keywords.extend(expanded.get("related", []))

        return response

# Usage
search = AdvancedSearchComponent()
results = await search.perform_advanced_search(
    query="fantasy",
    user_id="user_123",
    filters={"genres": ["Fantasy", "Adventure"]}
)
```

### Example 3: Autocomplete with N-grams

```python
from app.utils.ngram import build_search_index, search_using_index
from app.services.book_service import get_book_service

class AutocompleteService:
    def __init__(self):
        self.book_service = get_book_service()
        self.index = None
        self.books = None
        self._build_index()

    def _build_index(self):
        """Build n-gram index for fast autocomplete."""
        self.books = self.book_service.get_all_books()
        titles = [b.title for b in self.books]
        self.index = build_search_index(titles, ngram_type="char", n=2)

    def autocomplete(self, partial_query: str, limit: int = 10):
        """Get autocomplete suggestions."""
        if not self.index or not self.books:
            return []

        results = search_using_index(
            partial_query,
            self.index,
            [b.title for b in self.books],
            ngram_type="char",
            n=2
        )

        return [title for title, _ in results[:limit]]

# Usage
autocomplete = AutocompleteService()

suggestions = autocomplete.autocomplete("har")
# Output: ["Harry Potter", "Harlequin Romance", ...]
```

---

## Summary

This implementation provides:

✅ **Flexible N-gram matching** for fuzzy search and typo tolerance
✅ **Modular service architecture** for easy testing and integration
✅ **AI-powered suggestions** using LangChain
✅ **Comprehensive filtering and ranking**
✅ **Search history and analytics**
✅ **Caching for performance**
✅ **RESTful API endpoints**

All components are designed for easy integration into existing FastAPI applications.
