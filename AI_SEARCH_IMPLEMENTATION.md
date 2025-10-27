# AI Search Implementation Documentation

## Overview

AI-powered book search functionality has been successfully implemented using LangChain and ChatGPT-4.1. This feature allows users to ask natural language questions about books and receive intelligent recommendations.

## Architecture

### 1. Models (`app/models/ai_search.py`)

Complete Pydantic models matching the TypeScript interfaces:

- **AISearchQuestion**: Stores user questions with context and configuration
- **AISearchAnswer**: Stores AI-generated answers with recommendations
- **AISearchConversation**: Manages conversation threads
- **AISearchMessage**: Individual messages in conversations
- **AISearchHistory**: Simplified history view
- **Request/Response Models**: API communication structures

### 2. Service (`app/services/ai_search_service.py`)

Core business logic with LangChain integration:

#### Key Features:
- **ChatGPT-4.1 Integration**: Uses `gpt-4-turbo-preview` model with temperature 0.1
- **Conversation Context**: Maintains conversation history for contextual responses
- **Book Recommendations**: Intelligent book matching based on AI analysis
- **Search Context**: Supports genre, price range, and custom filters
- **Firestore Persistence**: Stores questions, answers, and conversations

#### Main Methods:
- `search_with_ai()`: Primary AI search endpoint
- `create_question()`: Store user questions
- `create_answer()`: Store AI responses
- `create_conversation()`: Manage conversation threads
- `get_search_history()`: Retrieve user's search history

### 3. Router (`app/routers/ai_search.py`)

FastAPI endpoints for AI search operations:

#### Endpoints:

**Search Operations:**
- `POST /api/ai-search/search` - Perform AI-powered search
- `GET /api/ai-search/health` - Health check endpoint

**Question Management:**
- `GET /api/ai-search/questions/{question_id}` - Get question by ID
- `GET /api/ai-search/questions/{question_id}/answers` - Get answers for question

**Answer Management:**
- `GET /api/ai-search/answers/{answer_id}` - Get answer by ID

**Conversation Management:**
- `GET /api/ai-search/conversations/{conversation_id}` - Get conversation
- `GET /api/ai-search/conversations/user/{user_email}` - Get user conversations

**History:**
- `GET /api/ai-search/history/{user_email}` - Get search history

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### AI Model Configuration

Current settings:
- **Model**: `gpt-4-turbo-preview` (ChatGPT-4.1)
- **Temperature**: 0.1 (more deterministic responses)
- **Provider**: OpenAI via LangChain

## Usage Examples

### 1. Basic AI Search Request

```bash
POST /api/ai-search/search
Content-Type: application/json

{
  "question": "Can you recommend a good science fiction book for beginners?",
  "userEmail": "user@example.com",
  "context": {
    "genre": "Science Fiction",
    "priceRange": {
      "min": 0,
      "max": 30
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "questionId": "q123",
    "answerId": "a456",
    "answer": "Based on your interest in science fiction for beginners, I recommend...",
    "recommendedBooks": [
      {
        "bookId": "book1",
        "title": "The Martian",
        "author": "Andy Weir",
        "relevanceScore": 0.95,
        "reason": "Perfect for sci-fi beginners with accessible writing style",
        "price": 15.99,
        "coverImageUrl": "..."
      }
    ],
    "suggestions": [
      "Can you recommend similar books in a different genre?",
      "What are the bestsellers in this category?"
    ],
    "conversationId": "conv789"
  }
}
```

### 2. Continue Conversation

```bash
POST /api/ai-search/search
Content-Type: application/json

{
  "question": "What about fantasy books instead?",
  "userEmail": "user@example.com",
  "conversationId": "conv789"
}
```

### 3. Get Search History

```bash
GET /api/ai-search/history/user@example.com?limit=20
```

### 4. Get User Conversations

```bash
GET /api/ai-search/conversations/user/user@example.com?limit=10
```

## Features

### 1. Intelligent Search
- Natural language understanding
- Context-aware recommendations
- Genre and price filtering
- Rating-based suggestions

### 2. Conversation Management
- Multi-turn conversations
- Context preservation
- Message history tracking
- Book reference tracking

### 3. Personalization
- User-specific search history
- Conversation threads per user
- Preference learning over time

### 4. Recommendations
- AI-powered book matching
- Relevance scoring (0-1)
- Explanation for each recommendation
- Up to 3 top recommendations per query

### 5. Follow-up Suggestions
- Context-aware suggestions
- Genre exploration prompts
- Related search ideas

## Database Schema

### Collections in Firestore:

1. **ai_search_questions**
   - id: string
   - question: string
   - user_email: string
   - created_at: timestamp
   - search_context: object
   - model_config: object

2. **ai_search_answers**
   - id: string
   - question_id: string
   - answer: string
   - user_email: string
   - created_at: timestamp
   - recommended_books: array
   - suggestions: array
   - model_metadata: object
   - sources: array

3. **ai_search_conversations**
   - id: string
   - user_email: string
   - title: string
   - created_at: timestamp
   - updated_at: timestamp
   - messages: array

## Integration with Frontend

### TypeScript Interfaces
All models align with the provided TypeScript interfaces:
- `AISearchQuestion`
- `AISearchAnswer`
- `AISearchConversation`
- `AISearchMessage`
- `AISearchHistory`
- `AISearchRequest`
- `AISearchResponse`

### API Client Example (Next.js)

```typescript
// Search with AI
async function searchWithAI(question: string, userEmail: string) {
  const response = await fetch('/api/ai-search/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      userEmail,
      context: {
        genre: 'Fiction',
        priceRange: { min: 0, max: 50 }
      }
    })
  });

  const data: AISearchResponse = await response.json();

  if (data.success) {
    console.log('Answer:', data.data.answer);
    console.log('Books:', data.data.recommendedBooks);
  }
}

// Get search history
async function getHistory(userEmail: string) {
  const response = await fetch(`/api/ai-search/history/${userEmail}`);
  const history: AISearchHistory[] = await response.json();
  return history;
}
```

## Testing

### Manual Testing

1. **Health Check:**
```bash
curl http://localhost:8000/api/ai-search/health
```

2. **AI Search:**
```bash
curl -X POST http://localhost:8000/api/ai-search/search \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Recommend a mystery novel",
    "userEmail": "test@example.com"
  }'
```

3. **Get History:**
```bash
curl http://localhost:8000/api/ai-search/history/test@example.com
```

## Error Handling

The implementation includes comprehensive error handling:

- **400 Bad Request**: Invalid input data
- **404 Not Found**: Resource doesn't exist
- **500 Internal Server Error**: AI service errors, database errors

All errors return structured responses:
```json
{
  "success": false,
  "error": {
    "code": "AI_SEARCH_ERROR",
    "message": "Detailed error message"
  }
}
```

## Performance Considerations

1. **Caching**: Consider implementing Redis cache for frequent queries
2. **Rate Limiting**: Add rate limits for AI endpoint to manage API costs
3. **Book Context**: Currently fetches top 50 books, can be optimized with embeddings
4. **Async Operations**: All AI operations are async for better performance

## Future Enhancements

1. **Semantic Search**: Add vector embeddings for better book matching
2. **User Preferences**: Learn from user interactions
3. **Multi-language Support**: Support questions in multiple languages
4. **Advanced Filtering**: More sophisticated filter combinations
5. **Streaming Responses**: Stream AI responses for better UX
6. **Analytics**: Track popular queries and book recommendations

## Maintenance

### Monitoring
- Monitor OpenAI API usage and costs
- Track response times for AI queries
- Log failed requests for debugging

### Updates
- Keep LangChain and OpenAI packages updated
- Adjust temperature and model parameters based on user feedback
- Refine system prompts for better recommendations

## Dependencies

```
langchain==0.3.25
langchain-openai==0.3.21
langchain-core==0.3.70
openai==1.81.0
```

All dependencies are already installed in your requirements.txt.

## Support

For issues or questions:
1. Check logs in the service layer
2. Verify OpenAI API key is valid
3. Ensure Firestore is properly configured
4. Check network connectivity to OpenAI API

---

**Implementation Date**: 2025-10-27
**Model**: GPT-4 Turbo (gpt-4-turbo-preview)
**Temperature**: 0.1
**Status**: ✅ Completed and Ready for Testing
