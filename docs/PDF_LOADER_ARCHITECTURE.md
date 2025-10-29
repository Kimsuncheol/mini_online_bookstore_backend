# PDF Loader Architecture Documentation

## Overview

This document describes the architecture and integration of PDF processing functionality across the Mini Online Bookstore backend. The PDF loader utility is strategically placed and shared across multiple services following a **separation of concerns** pattern.

---

## Core Components

### 1. PDF Loader Utility (`app/utils/pdf_loader.py`)

**Responsibility**: Low-level PDF processing and Firebase Storage integration

**Key Functions**:
- `download_pdf_from_storage()` - Download raw bytes from Firebase Storage
- `load_pdf_from_storage()` - Load PDF pages as LangChain Documents
- `load_and_split_pdf_from_storage()` - Load and intelligently split PDF text
- `split_pdf_text()` - Recursive character-based text splitting
- `load_pdf_from_local_path()` - Local file support for development

**Technology Stack**:
- **PyMuPDFLoader**: Extracts PDF pages
- **RecursiveCharacterTextSplitter**: Intelligent text chunking with 4-level hierarchy:
  1. Paragraph breaks (`\n\n`)
  2. Line breaks (`\n`)
  3. Word boundaries (` `)
  4. Character level (fallback)
- **Firebase Storage**: PDF file storage backend

**Parameters**:
- `chunk_size`: Target chunk size in characters (default: 1000)
- `chunk_overlap`: Overlap between chunks for context preservation (default: 200)

**Error Handling**:
- `PDFLoaderError`: Base exception class
- `PDFNotFoundError`: File not found in storage
- `PDFProcessingError`: PDF parsing or splitting failures

---

### 2. Book Service (`app/services/book_service.py`)

**Responsibility**: Orchestration of PDF operations with book context

**PDF-Related Methods** (Lines 52-218):

#### a. `download_book_pdf(book_or_id, raise_errors=False)`
- Downloads raw PDF bytes
- Handles book ID-to-Book conversion
- Returns `None` on error (unless `raise_errors=True`)

#### b. `load_book_pdf_documents(book_or_id, raise_errors=False)`
- Loads PDF as LangChain Documents without splitting
- Preserves document structure and metadata
- Each page becomes a separate Document

#### c. `load_and_split_book_pdf(book_or_id, chunk_size=1000, chunk_overlap=200, raise_errors=False)`
- Loads and splits PDF in one operation
- Returns list of semantically coherent chunks
- Maintains metadata across chunks

#### d. `get_pdf_preview_text(book_or_id, max_chars=2000, chunk_size=900, chunk_overlap=150)`
- Extracts first `max_chars` of text from PDF
- Used by summary and search services for context
- Returns `None` on error

**Helper Methods**:

#### `_ensure_book_instance(book_or_id: Union[Book, str])`
- Converts book ID string to Book object
- Handles both types of input
- Returns `None` if book not found

#### `_resolve_pdf_storage_path(book: Book)`
- Gets Firebase Storage path from book
- Uses `pdf_file_name` field
- Returns `None` if no path available

#### `_extract_path_from_pdf_url(pdf_url: str)`
- Parses PDF URLs to extract storage paths
- Handles URL-encoded paths
- Returns cleaned path string

**Constants**:
```python
DEFAULT_PDF_CHUNK_SIZE = 1000
DEFAULT_PDF_CHUNK_OVERLAP = 200
DEFAULT_PDF_PREVIEW_CHARS = 2000
```

---

### 3. Integration with Other Services

#### A. Book Summary Service (`book_summary_service.py`)

**Integration Point** (Line 325-333):
```python
book_service = self._get_book_service()
if book_service:
    pdf_preview = book_service.get_pdf_preview_text(
        book,
        max_chars=1000,
        chunk_size=900,
        chunk_overlap=150,
    )
```

**Usage**:
- Retrieves PDF preview text (first ~1000 chars)
- Uses preview as context for AI summary generation
- Enhances GPT-4 summaries with actual book content

**Data Flow**:
1. Book Summary Service requests PDF preview from Book Service
2. Book Service invokes PDF loader utility
3. Preview text incorporated into system prompt for ChatGPT
4. AI generates context-aware summary

#### B. AI Search Service (`ai_search_service.py`)

**Integration Points** (Line 826-831):
```python
preview_text = self.book_service.get_pdf_preview_text(
    book,
    max_chars=600,
    chunk_size=700,
    chunk_overlap=120,
)
if preview_text:
    book_data["pdf_preview"] = preview_text
```

**Usage**:
- Extracts PDF previews for top 3 books only (performance optimization)
- Includes preview snippets in AI book recommendations
- Provides context for generating relevant suggestions

**Data Flow**:
1. AI Search queries for relevant books
2. For top 3 results, retrieves PDF preview via Book Service
3. Preview embedded in books_catalog for ChatGPT context
4. GPT-4 generates better recommendations with book content context

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│          PDF Loader Utility (Low-level)                 │
│  app/utils/pdf_loader.py                                │
│  - PyMuPDFLoader integration                            │
│  - Firebase Storage communication                        │
│  - RecursiveCharacterTextSplitter                       │
└────────────────┬────────────────────────────────────────┘
                 │
                 │ Used by
                 ▼
┌─────────────────────────────────────────────────────────┐
│          Book Service (Orchestration Layer)              │
│  app/services/book_service.py                           │
│  - download_book_pdf()                                  │
│  - load_book_pdf_documents()                            │
│  - load_and_split_book_pdf()                            │
│  - get_pdf_preview_text()                               │
│  - Path resolution helpers                              │
└──┬──────────────────────────────────┬──────────────────┬┘
   │                                  │                  │
   │ get_pdf_preview_text()           │                  │
   ▼                                  ▼                  ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌───────────┐
│ Book Summary Service │  │  AI Search Service   │  │ Book API  │
│ Generates summaries  │  │  Recommends books    │  │  Routes   │
│ with PDF context     │  │  with preview text   │  │           │
└──────────────────────┘  └──────────────────────┘  └───────────┘
```

---

## Design Decisions Explained

### 1. **Centralized in Book Service (Why?)**

✅ **Single Source of Truth**
- All PDF access routes through Book Service
- Consistent error handling and logging
- Easy to add caching strategies

✅ **Loose Coupling**
- Summary and Search services don't depend on PDF loader directly
- Changes to PDF processing only affect Book Service
- Easy to swap implementations (Firebase → S3, etc.)

✅ **Performance Control**
- Book Service can apply heuristics (preview-only for expensive ops)
- Can implement caching at service level
- Rate limiting possible for external integrations

✅ **Separation of Concerns**
- Book Service: "How to get book data + PDF"
- Summary Service: "How to generate AI summaries"
- Search Service: "How to find relevant books"

### 2. **Why NOT Spread Across All Services?**

❌ **Avoid Tight Coupling**
- If every service imported PDF loader directly, changes break multiple services

❌ **Code Duplication**
- Path resolution logic would be duplicated
- Error handling would be inconsistent

❌ **Firebase Integration Complexity**
- Firebase credentials and bucket access should be centralized
- Only Book Service needs to know about Firebase Storage paths

---

## Data Flow Examples

### Example 1: PDF Preview for AI Summary

```
HTTP Request: POST /api/books/{book_id}/summaries (force_regenerate=true)
     │
     ├─> BookController routes to BookSummaryService
     │
     ├─> BookSummaryService.generate_summary_for_book(book)
     │     │
     │     ├─> Calls BookService._get_book_service()
     │     │
     │     └─> BookService.get_pdf_preview_text(book, max_chars=1000)
     │           │
     │           ├─> BookService._resolve_pdf_storage_path(book)
     │           │     Returns: "pdfs/book_123.pdf" (from book.pdf_file_name)
     │           │
     │           └─> pdf_loader.load_and_split_pdf_from_storage(path)
     │                 │
     │                 ├─> download_pdf_from_storage(path)
     │                 │     Returns: bytes from Firebase Storage
     │                 │
     │                 ├─> PyMuPDFLoader(temp_file).load()
     │                 │     Returns: [Document(page1), Document(page2), ...]
     │                 │
     │                 └─> split_pdf_text(docs, chunk_size=900)
     │                       Returns: [Chunk1, Chunk2, ..., ChunkN]
     │
     ├─> Extract first 1000 chars from chunks
     │
     ├─> Include preview in system prompt for ChatGPT
     │
     └─> Generate AI summary with book content context
```

### Example 2: PDF Preview for Book Search Recommendations

```
HTTP Request: POST /api/ai-search/chat
     │
     ├─> AISearchController routes to AISearchService
     │
     ├─> AISearchService.search_with_ai(question, user_email)
     │     │
     │     ├─> AISearchService._get_books_context(context)
     │     │     │
     │     │     ├─> BookService.get_featured_books(limit=20)
     │     │     │
     │     │     └─> For each of top 3 books:
     │     │           BookService.get_pdf_preview_text(book, max_chars=600)
     │     │           Returns: preview text
     │     │
     │     ├─> Format books_catalog with previews
     │     │
     │     ├─> AISearchService._generate_ai_response(question, books_context)
     │     │     ChatGPT analyzes catalog with previews
     │     │
     │     └─> Generate recommendations with better context
     │
     └─> Return recommended books + suggestions
```

---

## Current Book Model Alignment

### TypeScript Interface → Python Models

The `Book` model in `app/models/book.py` fully implements the TypeScript interface:

**Core Fields** ✅
- `id`: str
- `title`: str
- `author`: str
- `isbn`: Optional[str]
- `description`: Optional[str]
- `genre`: str
- `language`: Optional[str]
- `published_date`: Optional[datetime]
- `page_count`: Optional[int]

**Pricing** ✅
- `price`: float
- `original_price`: Optional[float]
- `currency`: Optional[str]
- `discount`: Optional[float]

**Media & PDF** ✅
- `cover_image`: Optional[str]
- `cover_image_url`: Optional[str]
- `pdf_url`: Optional[str]
- `pdf_file_name`: Optional[str] ← **Used by Book Service for PDF location**

**Ratings** ✅
- `rating`: Optional[float]
- `review_count`: Optional[int]

**Publishing** ✅
- `publisher`: Optional[str]
- `edition`: Optional[str]

**Metadata** ✅
- `in_stock`: bool
- `stock_quantity`: int
- `is_new`: bool
- `is_featured`: bool
- `created_at`: datetime
- `updated_at`: datetime

**Configuration** ✅
- `ConfigDict` with camelCase serialization
- `populate_by_name` for flexible input
- `from_attributes` for Firestore mapping

---

## Recommendations & Best Practices

### 1. PDF Preview Extraction

**Current Best Practice**:
```python
# For AI summaries: larger context
pdf_preview = book_service.get_pdf_preview_text(
    book,
    max_chars=1000,    # Generous for summary context
    chunk_size=900,
    chunk_overlap=150
)

# For search recommendations: smaller, faster
pdf_preview = book_service.get_pdf_preview_text(
    book,
    max_chars=600,     # Limited to top 3 books only
    chunk_size=700,
    chunk_overlap=120
)
```

### 2. Error Handling Pattern

**Book Service Pattern**:
```python
def get_pdf_preview_text(self, book_or_id, max_chars=2000, ...):
    try:
        # PDF operations
        documents = self.load_and_split_book_pdf(book_or_id, ...)
        return text[:max_chars]
    except PDFNotFoundError:
        return None  # Graceful degradation
    except (PDFLoaderError, PDFProcessingError) as exc:
        print(f"Warning: PDF extraction failed: {str(exc)}")
        return None  # Don't break dependent service
```

### 3. Performance Considerations

**Current Optimizations**:
- ✅ Preview-only extraction (not full PDF processing)
- ✅ Limited to top 3 books in search service
- ✅ Configurable chunk sizes for different use cases
- ✅ Overlap strategy maintains context across chunks

**Future Optimization Opportunities**:
- 🔄 Cache extracted previews in Firestore
- 🔄 Lazy-load previews (on-demand, not pre-computation)
- 🔄 Background job for popular books
- 🔄 Redis cache for frequently accessed previews

---

## Migration Guide (If Needed)

### Adding PDF Processing to a New Service

If you need to add PDF functionality to a new service:

**✅ DO THIS**:
```python
from app.services.book_service import get_book_service

class MyNewService:
    def __init__(self):
        self.book_service = get_book_service()

    def some_method(self, book_id):
        preview = self.book_service.get_pdf_preview_text(book_id)
        # Use preview
```

**❌ DON'T DO THIS**:
```python
# Don't import pdf_loader directly
from app.utils.pdf_loader import load_pdf_from_storage

# This creates tight coupling and duplicates path resolution logic
```

---

## Testing & Validation

### Unit Tests Should Cover:

1. **PDF Loader Utility**
   - Loading local PDFs
   - Text splitting consistency
   - Error handling for corrupt files

2. **Book Service Integration**
   - Book ID to Book conversion
   - Firebase Storage path resolution
   - URL parsing for pdf_url field
   - Preview text extraction

3. **Service Integration**
   - Summary Service can retrieve previews
   - Search Service can get previews for top books
   - Graceful degradation on PDF errors

---

## Troubleshooting

### PDF Not Found Errors

1. Check `book.pdf_file_name` is set correctly
2. Verify Firebase Storage path exists
3. Check Firebase credentials are valid
4. Review Books Collection has correct document

### PDF Processing Slow

1. Check `chunk_overlap` isn't too large
2. Consider caching preview text
3. For search, ensure limit=3 for preview extraction
4. Monitor PDF file sizes

### Memory Issues with Large PDFs

1. Use `load_and_split_pdf_from_storage()` instead of loading entire PDF
2. Reduce `chunk_size` for better memory efficiency
3. Process in batches rather than all books at once

---

## Summary

**Current Architecture Status**: ✅ **OPTIMALLY STRUCTURED**

| Aspect | Status | Details |
|--------|--------|---------|
| **PDF Loader Utility** | ✅ Complete | Low-level Firebase + PyMuPDF integration |
| **Book Service Integration** | ✅ Complete | 4 PDF methods + 3 helper methods |
| **Summary Service Usage** | ✅ Complete | Uses preview for AI context |
| **Search Service Usage** | ✅ Complete | Uses preview for recommendations |
| **Book Model** | ✅ Complete | Fully aligned with TypeScript interface |
| **Error Handling** | ✅ Robust | Graceful degradation across services |
| **Performance** | ✅ Optimized | Preview-only, limited extraction |

**No refactoring needed.** The current architecture properly separates concerns while maintaining loose coupling between services.
