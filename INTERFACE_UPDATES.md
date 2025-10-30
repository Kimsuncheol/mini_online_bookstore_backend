# Interface Updates - Search Models and Services

Updated the search models and services to align with the client-side TypeScript interfaces from the Next.js application.

---

## Updated Interfaces

### SearchHistoryItem
**Changed from:**
```typescript
{
  id: string
  query: string
  timestamp: datetime
  user_id?: string
  result_count: int
  search_type?: string
}
```

**Changed to:**
```typescript
{
  id: string
  query: string
  timestamp: number          // Unix timestamp in milliseconds
  userEmail?: string         // Changed from user_id
}
```

### SearchResult
**Changed from:**
```typescript
{
  id: string
  title: string
  type: 'book' | 'author' | 'category'
  subtitle?: string
  image_url?: string
  url: string
  relevance_score?: number
  description?: string
  metadata?: object
}
```

**Changed to:**
```typescript
{
  id: string
  title: string
  type: 'book' | 'author' | 'category'
  subtitle?: string
  imageUrl?: string          // Changed from image_url
  url: string
}
```

### SearchSettings
**Changed from:**
```typescript
{
  history_enabled: boolean
  fuzzy_matching: boolean
  include_suggestions: boolean
  fuzzy_threshold: number
  max_suggestions: number
}
```

**Changed to:**
```typescript
{
  historyEnabled: boolean    // Only this field, rest removed
}
```

---

## Updated Models (`app/models/search.py`)

### 1. SearchHistoryItem
```python
class SearchHistoryItem(BaseModel):
    id: str
    query: str
    timestamp: int  # Unix timestamp in milliseconds (was datetime)
    user_email: Optional[str]  # Changed from user_id
```

### 2. SearchHistoryCreate
```python
class SearchHistoryCreate(BaseModel):
    query: str
    timestamp: int  # Unix timestamp in milliseconds
    user_email: Optional[str]  # Changed from user_id
    # Removed: result_count, search_type
```

### 3. SearchResult
```python
class SearchResult(BaseModel):
    id: str
    title: str
    type: Literal["book", "author", "category"]
    subtitle: Optional[str]
    image_url: Optional[str]  # Kept field, camelCase conversion via alias_generator
    url: str
    # Removed: relevance_score, description, metadata
```

### 4. SearchSettings
```python
class SearchSettings(BaseModel):
    history_enabled: bool  # Only field
    # Removed: fuzzy_matching, include_suggestions, fuzzy_threshold, max_suggestions
```

### 5. SearchAnalytics
```python
class SearchAnalytics(BaseModel):
    ...
    user_email: Optional[str]  # Changed from user_id
    ...
```

---

## Updated Services (`app/services/search_service.py`)

### SearchService Changes

#### 1. _save_search_history()
**Before:**
```python
async def _save_search_history(
    self,
    query: str,
    user_id: Optional[str],
    result_count: int,
    search_type: str = "all",
) -> None:
```

**After:**
```python
async def _save_search_history(
    self,
    query: str,
    user_email: Optional[str],
) -> None:
    # Converts datetime to Unix timestamp in milliseconds
    timestamp_ms = int(datetime.now().timestamp() * 1000)
    # Uses user_email as document key instead of user_id
```

#### 2. get_search_history()
**Before:**
```python
def get_search_history(
    self,
    user_id: str,
    limit: int = 20,
) -> List[SearchHistoryItem]:
    # Returns: query, timestamp (datetime), user_id, result_count, search_type
```

**After:**
```python
def get_search_history(
    self,
    user_email: str,
    limit: int = 20,
) -> List[SearchHistoryItem]:
    # Returns: query, timestamp (int - milliseconds), user_email
    # Converts stored timestamps to milliseconds if needed
```

#### 3. clear_search_history()
**Before:**
```python
def clear_search_history(self, user_id: str) -> bool:
```

**After:**
```python
def clear_search_history(self, user_email: str) -> bool:
```

#### 4. _save_search_analytics()
**Before:**
```python
async def _save_search_analytics(
    self,
    query: str,
    result_count: int,
    processing_time_ms: int,
    user_id: Optional[str],
    search_type: str,
    had_results: bool,
) -> None:
```

**After:**
```python
async def _save_search_analytics(
    self,
    query: str,
    result_count: int,
    processing_time_ms: int,
    user_email: Optional[str],  # Changed from user_id
    search_type: str,
    had_results: bool,
) -> None:
```

#### 5. search() method
**Before:**
```python
await self._save_search_history(
    query=query,
    user_id=request.user_id,
    result_count=total_count,
    search_type=request.search_type,
)

await self._save_search_analytics(
    query=query,
    result_count=total_count,
    processing_time_ms=processing_time,
    user_id=request.user_id,
    search_type=request.search_type,
    had_results=total_count > 0,
)
```

**After:**
```python
await self._save_search_history(
    query=query,
    user_email=request.user_email,  # Changed from user_id
)

await self._save_search_analytics(
    query=query,
    result_count=total_count,
    processing_time_ms=processing_time,
    user_email=request.user_email,  # Changed from user_id
    search_type=request.search_type,
    had_results=total_count > 0,
)
```

### SearchRequest Changes
**Before:**
```python
class SearchRequest(BaseModel):
    ...
    user_id: Optional[str]  # For personalized search
```

**After:**
```python
class SearchRequest(BaseModel):
    ...
    user_email: Optional[str]  # Changed from user_id
```

---

## Updated Router (`app/routers/search.py`)

### GET /search/history/{user_email}
**Before:**
```python
@router.get("/history/{user_id}", response_model=List[SearchHistoryItem])
def get_search_history(
    user_id: str,
    limit: Optional[int] = Query(20, ge=1, le=100),
) -> List[SearchHistoryItem]:
```

**After:**
```python
@router.get("/history/{user_email}", response_model=List[SearchHistoryItem])
def get_search_history(
    user_email: str,
    limit: Optional[int] = Query(20, ge=1, le=100),
) -> List[SearchHistoryItem]:
```

### DELETE /search/history/{user_email}
**Before:**
```python
@router.delete("/history/{user_id}")
def clear_search_history(user_id: str) -> dict:
```

**After:**
```python
@router.delete("/history/{user_email}")
def clear_search_history(user_email: str) -> dict:
```

---

## Key Changes Summary

### Data Type Changes
- `user_id` → `user_email` (string, email format)
- `timestamp: datetime` → `timestamp: int` (Unix milliseconds)
- Removed: `result_count`, `search_type`, `relevance_score`, `description`, `metadata`
- Removed from SearchSettings: `fuzzy_matching`, `include_suggestions`, `fuzzy_threshold`, `max_suggestions`

### Storage Changes
- Search history documents now use `user_email` as the key instead of `user_id`
- Timestamps stored as Unix milliseconds (integer)
- Simplified data structure for search history items

### API Changes
- `/search/history/{user_id}` → `/search/history/{user_email}`
- `/search/history/{user_id}` (DELETE) → `/search/history/{user_email}` (DELETE)
- SearchRequest now uses `user_email` instead of `user_id`

---

## Timestamp Conversion

### To Unix Milliseconds (saving):
```python
timestamp_ms = int(datetime.now().timestamp() * 1000)
```

### From Unix Milliseconds (reading):
```python
timestamp_ms = data.get("timestamp", int(datetime.now().timestamp() * 1000))
```

---

## Implementation Notes

1. **Camel Case Conversion**: The `alias_generator=to_camel` configuration ensures:
   - `user_email` → `userEmail` in JSON responses
   - `image_url` → `imageUrl` in JSON responses
   - `history_enabled` → `historyEnabled` in JSON responses

2. **Backward Compatibility**: None - these are breaking changes to align with client interfaces

3. **Database Migration**: Existing search history data using `user_id` will need to be migrated or the service will need to handle both formats during a transition period

4. **Timestamp Storage**: All new timestamps are stored as Unix milliseconds (integers) for consistency with JavaScript/client expectations

---

## Files Updated

1. ✅ `app/models/search.py` - Updated models
2. ✅ `app/services/search_service.py` - Updated service methods and logic
3. ✅ `app/routers/search.py` - Updated endpoint paths and parameters

---

## Verification

All changes have been applied to:
- SearchHistoryItem model
- SearchHistoryCreate model
- SearchResult model
- SearchSettings model
- SearchRequest model
- SearchAnalytics model
- SearchService methods
- Search API endpoints

The models and services are now aligned with the client-side TypeScript interfaces.
