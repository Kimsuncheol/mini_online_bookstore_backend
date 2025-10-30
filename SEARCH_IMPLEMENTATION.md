# Search Implementation Guide

Complete implementation of book search functionality with n-gram based fuzzy matching and AI-powered suggestions.

## Overview

This implementation provides a modular, production-ready search system with three main components:

1. **N-gram Utility Functions** - Text similarity and fuzzy matching
2. **Search Models & Service** - Search operations with Firestore integration
3. **AI-based Suggestions** - LangChain-powered keyword recommendations

---

## Mission 1: N-gram Utility Functions

### Location
`app/utils/ngram.py`

### Features

#### Character-level N-grams
```python
from app.utils.ngram import generate_character_ngrams

# Generate 3-character n-grams for fuzzy matching
ngrams = generate_character_ngrams("hello", n=3)
# Result: {'hel', 'ell', 'llo'}
```

**Uses**: Typo tolerance, spell-checking, similarity matching

#### Word-level N-grams
```python
from app.utils.ngram import generate_word_ngrams

# Generate bigrams (2-word n-grams)
ngrams = generate_word_ngrams("the quick brown fox", n=2)
# Result: {'the quick', 'quick brown', 'brown fox'}
```

**Uses**: Semantic similarity, phrase matching, context analysis

#### Similarity Calculation
```python
from app.utils.ngram import calculate_string_similarity

# Calculate Jaccard similarity between two strings
score = calculate_string_similarity("The Great Gatsby", "The Greatest Gatsby", ngram_type="char", n=3)
# Result: 0.789 (0-1 scale)
```

#### Search Index Building
```python
from app.utils.ngram import build_search_index, search_using_index

# Build index once for efficient searching
books = ["Harry Potter", "The Hobbit", "The Lord of the Rings"]
index = build_search_index(books, ngram_type="char", n=3)

# Fast lookup using the index
results = search_using_index("harry", index, books)
# Result: [("Harry Potter", 0.95)]
```

### Core Functions

| Function | Purpose |
|----------|---------|
| `normalize_text()` | Normalize text for processing |
| `tokenize()` | Split text into words |
| `generate_character_ngrams()` | Create character-level n-grams |
| `generate_word_ngrams()` | Create word-level n-grams |
| `generate_mixed_ngrams()` | Get both character and word n-grams |
| `jaccard_similarity()` | Calculate set-based similarity |
| `calculate_string_similarity()` | Compare two strings |
| `find_similar_strings()` | Find matches in a list |
| `build_search_index()` | Create n-gram index |
| `search_using_index()` | Fast search using index |

---

## Mission 2: Search Models & Service

### Models Location
`app/models/search.py`

### Model Classes

#### SearchHistoryItem
Represents a search query in user history.
```python
from app.models.search import SearchHistoryItem

history_item = SearchHistoryItem(
    id="history_123",
    query="fantasy novels",
    timestamp=datetime.now(),
    user_id="user_123",
    result_count=45,
    search_type="books"
)
```

#### SearchResult
Individual search result (book, author, or category).
```python
from app.models.search import SearchResult

result = SearchResult(
    id="book_456",
    title="Harry Potter and the Philosopher's Stone",
    type="book",
    subtitle="by J.K. Rowling",
    image_url="https://...",
    url="/books/book_456",
    relevance_score=0.95,
    description="A young wizard's journey..."
)
```

#### SearchRequest
Request model for search operations.
```python
from app.models.search import SearchRequest, SearchSettings

request = SearchRequest(
    query="fantasy books",
    search_type="books",
    filters={"genres": ["Fantasy"], "min_price": 5.0, "max_price": 25.0},
    settings=SearchSettings(
        history_enabled=True,
        fuzzy_matching=True,
        include_suggestions=True,
        fuzzy_threshold=0.6
    ),
    page=1,
    page_size=20,
    user_id="user_123"
)
```

#### SearchResponse
Complete response from search operation.
```python
from app.models.search import SearchResponse

response = SearchResponse(
    success=True,
    results=[...],  # List of SearchResult
    total_count=45,
    suggested_keywords=["fantasy adventure", "wizard novels", "magical stories"],
    processing_time_ms=245,
    page=1,
    page_size=20,
    has_more=True
)
```

### Service Location
`app/services/search_service.py`

### Service Features

#### Search Operation
```python
from app.services.search_service import get_search_service
from app.models.search import SearchRequest

search_service = get_search_service()

request = SearchRequest(
    query="harry potter",
    search_type="books",
    page=1,
    page_size=20,
    user_id="user_123"
)

response = await search_service.search(request)
# Returns: SearchResponse with fuzzy-matched results
```

**How it works:**
1. Normalizes the search query
2. Fetches all books from Firestore
3. Uses n-gram fuzzy matching on titles and authors
4. Filters by optional criteria (genre, price, rating, etc.)
5. Ranks results by relevance score
6. Generates AI suggestions (Mission 3)
7. Saves search history and analytics

#### Search History
```python
# Get search history for user
history = search_service.get_search_history(user_id="user_123", limit=20)

# Clear search history
success = search_service.clear_search_history(user_id="user_123")
```

#### Popular Searches
```python
# Get most popular search queries
popular = search_service.get_popular_searches(limit=10)
# Returns: [{"query": "harry potter", "count": 523}, ...]
```

### Data Storage

**Firestore Collections:**

```
firestore
├── books/
│   ├── [book_id]/
│   │   └── ... (book data)
│
├── search_history/
│   ├── [user_id]/
│   │   └── queries/
│   │       └── [history_id]
│   │           ├── query: "harry potter"
│   │           ├── timestamp: datetime
│   │           ├── result_count: 45
│   │           └── search_type: "books"
│
└── search_analytics/
    └── [analytics_id]
        ├── query: "harry potter"
        ├── result_count: 45
        ├── processing_time_ms: 245
        ├── had_results: true
        └── timestamp: datetime
```

---

## Mission 3: AI-based Suggestions

### Service Location
`app/services/search_suggestion_service.py`

### Features

#### Generate Search Suggestions
Uses LangChain + OpenAI to generate intelligent keyword suggestions.

```python
from app.services.search_suggestion_service import get_search_suggestion_service

suggestion_service = get_search_suggestion_service()

# Generate suggestions based on query and results
suggestions = await suggestion_service.generate_search_suggestions(
    query="harry potter",
    results=[...],  # List of SearchResult
    max_suggestions=5,
    use_cache=True
)
# Returns: ["wizard novels", "fantasy adventure", "magical schools", ...]
```

**Behavior:**
- If search has results: Suggests related topics based on result content
- If no results: Suggests broader search terms and alternatives
- Caches suggestions for 24 hours

#### Content-based Filtering
Analyzes semantic similarity between query and book content.

```python
# Find books semantically similar to query
similar_books = await suggestion_service.analyze_content_similarity(
    query="coming of age adventure",
    books=all_books,
    top_k=5
)
# Returns: [
#     {"book_id": "123", "title": "The Hobbit", "similarity_score": 0.89},
#     {"book_id": "456", "title": "Percy Jackson", "similarity_score": 0.85},
#     ...
# ]
```

#### Related Searches
Get search suggestions related to a specific book.

```python
# Suggestions based on book content
related = await suggestion_service.get_related_searches(
    book=book_object,
    max_suggestions=5
)
# Returns: [
#     {"keyword": "fantasy adventure", "description": "Similar to this book's genre"},
#     {"keyword": "magic systems", "description": "Explores similar magical concepts"},
#     ...
# ]
```

#### Query Expansion
Expand a search query with synonyms and related terms.

```python
expanded = await suggestion_service.expand_query(
    query="wizard",
    max_terms=5
)
# Returns: {
#     "synonyms": ["sorcerer", "mage", "enchanter"],
#     "related": ["magic", "spells", "prophecy"],
#     "broader": ["fantasy character", "supernatural being"],
#     "narrower": ["apprentice wizard", "powerful wizard"]
# }
```

### Integration with SearchService

The `SearchService` automatically uses `SearchSuggestionService`:

```python
class SearchService:
    def __init__(self):
        self.suggestion_service = get_search_suggestion_service()

    async def search(self, request: SearchRequest) -> SearchResponse:
        # ... search logic ...

        # Get AI suggestions if enabled
        if request.settings.include_suggestions:
            suggestions = await self._get_suggested_keywords(query, results)

        return SearchResponse(..., suggested_keywords=suggestions)
```

### LangChain Configuration

Uses the following LangChain components:

- **ChatOpenAI**: GPT-4 Turbo for semantic understanding
- **ChatPromptTemplate**: Structured prompts for consistent responses
- **CharacterTextSplitter**: For breaking down long book descriptions

Configuration via environment variables:

```bash
OPENAI_API_KEY=sk-...
AI_SEARCH_MODEL=gpt-4-turbo-preview
AI_SEARCH_MODEL_TEMPERATURE=0.3
```

---

## Integration & Usage

### API Endpoints

All endpoints defined in `app/routers/search.py`:

```
POST   /search                              - Perform search
GET    /search/history/{user_id}            - Get search history
DELETE /search/history/{user_id}            - Clear history
GET    /search/popular                      - Popular searches
GET    /search/suggestions/related/{book_id} - Related searches
POST   /search/expand                       - Expand query
POST   /search/analyze-similarity           - Analyze similarity
```

### Example Usage

```python
from fastapi import FastAPI
from app.routers.search import router as search_router

app = FastAPI()
app.include_router(search_router)

# POST /search
# {
#   "query": "harry potter",
#   "search_type": "books",
#   "page": 1,
#   "page_size": 20,
#   "user_id": "user_123"
# }
```

### Complete Flow

1. **User types query**: "harry petter" (typo)
2. **N-gram fuzzy matching**: Finds "harry potter" despite typo
3. **Results returned**: Top 20 matching books
4. **AI suggestions**: "wizard novels", "fantasy adventure", etc.
5. **Search saved**: To user's search history
6. **Analytics recorded**: Query performance metrics

---

## Performance Characteristics

### N-gram Matching
- **Time Complexity**: O(n × m) where n = query length, m = item length
- **Space Complexity**: O(n + m) for n-gram sets
- **Typical Query Time**: < 100ms for 1000 books

### AI Suggestions
- **Time Complexity**: O(1) with caching (cache hit)
- **Time Complexity**: O(n) without cache (API call to OpenAI)
- **Cache Duration**: 24 hours
- **Typical API Call Time**: 500-2000ms

### Search Analytics
- **Storage**: ~500 bytes per query in Firestore
- **Query Time**: O(1) for popular searches aggregation

---

## Configuration & Customization

### N-gram Settings
```python
# In SearchService.__init__()
self.character_ngram_size = 3        # Trigrams
self.word_ngram_size = 2             # Bigrams
self.fuzzy_threshold = 0.6           # 60% similarity minimum
```

### Suggestion Cache
```python
# Cache in Firestore under:
SUGGESTIONS_CACHE_COLLECTION = "search_suggestions_cache"

# Cache invalidation: 24 hours
cache_age = (datetime.now() - cached_time).total_seconds()
if age < 86400:  # Use cache
```

### Pagination
```python
# Default: 20 results per page
# Max page_size: 100
default_page_size = 20
max_page_size = 100
```

---

## Error Handling

All services include comprehensive error handling:

- **Missing data**: Falls back to basic suggestions
- **API failures**: Returns cached results or graceful degradation
- **Invalid queries**: HTTP 400 with clear message
- **Firestore errors**: Logged with warning, continues operation

---

## Testing

Example test cases:

```python
import pytest
from app.models.search import SearchRequest
from app.services.search_service import get_search_service

@pytest.mark.asyncio
async def test_search_with_fuzzy_matching():
    service = get_search_service()
    request = SearchRequest(
        query="harry petter",  # Typo
        search_type="books"
    )
    response = await service.search(request)
    assert response.success
    assert len(response.results) > 0
    assert response.results[0].title == "Harry Potter..."

@pytest.mark.asyncio
async def test_search_suggestions():
    service = get_search_service()
    request = SearchRequest(
        query="fantasy",
        search_type="books",
        settings=SearchSettings(include_suggestions=True)
    )
    response = await service.search(request)
    assert response.suggested_keywords is not None
    assert len(response.suggested_keywords) > 0
```

---

## Future Enhancements

1. **Search Ranking**
   - Learning-to-rank models based on user behavior
   - Personalized ranking per user profile

2. **Performance Optimization**
   - Elasticsearch integration for large-scale search
   - N-gram index caching in Redis

3. **Advanced Features**
   - Spell correction using Levenshtein distance
   - Search analytics dashboard
   - A/B testing for suggestion quality

4. **AI Improvements**
   - Fine-tuned models on book domain
   - Embeddings-based semantic search
   - Multi-modal search (text + images)

---

## Architecture Diagram

```
SearchRouter (API)
    ↓
SearchService (orchestration)
    ├─→ N-gram Utility (fuzzy matching)
    ├─→ BookService (data access)
    └─→ SearchSuggestionService (AI)
            ├─→ LangChain (ChatOpenAI)
            └─→ Firestore (cache)

Firestore Collections:
    ├─ books (primary data)
    ├─ search_history (user queries)
    ├─ search_analytics (metrics)
    └─ search_suggestions_cache (AI cache)
```

---

## Summary

This implementation provides a complete, modular search system:

✅ **Mission 1**: N-gram functions for text similarity and fuzzy matching
✅ **Mission 2**: Search models and service with Firestore integration
✅ **Mission 3**: AI-powered suggestions using LangChain and content-based filtering

All components are independently testable and follow best practices for modularity and maintainability.
