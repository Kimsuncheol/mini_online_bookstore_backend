"""
AI Search Router

Handles AI-powered book search operations including:
- AI search queries with LangChain
- Question and answer management
- Conversation management
- Search history
"""

from fastapi import APIRouter, HTTPException, Path, Query
from typing import Optional, List

from app.models.ai_search import (
    AISearchRequest,
    AISearchResponse,
    AISearchResponseData,
    AISearchErrorData,
    AISearchQuestion,
    AISearchAnswer,
    AISearchConversation,
    AISearchHistory,
)
from app.services.ai_search_service import get_ai_search_service

router = APIRouter(prefix="/api/ai-search", tags=["ai-search"])


# ==================== AI SEARCH ENDPOINTS ====================


@router.post("/search", response_model=AISearchResponse)
async def search_with_ai(request: AISearchRequest):
    """
    Perform AI-powered book search using LangChain and ChatGPT-4.1.

    This endpoint:
    - Accepts a natural language question about books
    - Uses AI to understand the query and search intent
    - Provides intelligent book recommendations
    - Generates follow-up suggestions
    - Maintains conversation context

    Args:
        request (AISearchRequest): Search request with question and context

    Returns:
        AISearchResponse: AI-generated answer with recommended books

    Raises:
        HTTPException: 400 if invalid data, 500 if error occurs
    """
    try:
        ai_search_service = get_ai_search_service()

        result = await ai_search_service.search_with_ai(
            question=request.question,
            user_email=request.user_email,
            context=request.context,
            conversation_id=request.conversation_id,
        )

        response_data = AISearchResponseData(
            question_id=result["question_id"],
            answer_id=result["answer_id"],
            answer=result["answer"],
            recommended_books=result["recommended_books"],
            suggestions=result["suggestions"],
            conversation_id=result.get("conversation_id"),
        )

        return AISearchResponse(success=True, data=response_data)

    except Exception as e:
        error_data = AISearchErrorData(
            code="AI_SEARCH_ERROR",
            message=f"Error performing AI search: {str(e)}",
        )
        return AISearchResponse(success=False, error=error_data)


# ==================== QUESTION ENDPOINTS ====================


@router.get("/questions/{question_id}", response_model=AISearchQuestion)
async def get_question(question_id: str = Path(..., description="The question ID")):
    """
    Fetch a specific question by its ID.

    Args:
        question_id (str): The unique identifier of the question

    Returns:
        AISearchQuestion: The question data

    Raises:
        HTTPException: 404 if question not found, 500 if error occurs
    """
    try:
        ai_search_service = get_ai_search_service()
        question = ai_search_service.get_question_by_id(question_id)

        if question is None:
            raise HTTPException(
                status_code=404,
                detail=f"Question with ID '{question_id}' not found",
            )

        return question

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching question: {str(e)}",
        )


# ==================== ANSWER ENDPOINTS ====================


@router.get("/answers/{answer_id}", response_model=AISearchAnswer)
async def get_answer(answer_id: str = Path(..., description="The answer ID")):
    """
    Fetch a specific answer by its ID.

    Args:
        answer_id (str): The unique identifier of the answer

    Returns:
        AISearchAnswer: The answer data with recommendations

    Raises:
        HTTPException: 404 if answer not found, 500 if error occurs
    """
    try:
        ai_search_service = get_ai_search_service()
        answer = ai_search_service.get_answer_by_id(answer_id)

        if answer is None:
            raise HTTPException(
                status_code=404,
                detail=f"Answer with ID '{answer_id}' not found",
            )

        return answer

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching answer: {str(e)}",
        )


@router.get("/questions/{question_id}/answers", response_model=List[AISearchAnswer])
async def get_answers_for_question(
    question_id: str = Path(..., description="The question ID")
):
    """
    Fetch all answers for a specific question.

    Args:
        question_id (str): The question ID

    Returns:
        List[AISearchAnswer]: List of answers for the question

    Raises:
        HTTPException: 500 if error occurs
    """
    try:
        ai_search_service = get_ai_search_service()
        answers = ai_search_service.get_answers_for_question(question_id)
        return answers

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching answers: {str(e)}",
        )


# ==================== CONVERSATION ENDPOINTS ====================


@router.get("/conversations/{conversation_id}", response_model=AISearchConversation)
async def get_conversation(
    conversation_id: str = Path(..., description="The conversation ID")
):
    """
    Fetch a conversation by its ID.

    Args:
        conversation_id (str): The unique identifier of the conversation

    Returns:
        AISearchConversation: The conversation with all messages

    Raises:
        HTTPException: 404 if conversation not found, 500 if error occurs
    """
    try:
        ai_search_service = get_ai_search_service()
        conversation = ai_search_service.get_conversation_by_id(conversation_id)

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation with ID '{conversation_id}' not found",
            )

        return conversation

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching conversation: {str(e)}",
        )


@router.get("/conversations/user/{user_email}", response_model=List[AISearchConversation])
async def get_user_conversations(
    user_email: str = Path(..., description="The user's email"),
    limit: int = Query(20, ge=1, le=100, description="Maximum conversations to return"),
):
    """
    Fetch all conversations for a specific user.

    Args:
        user_email (str): The user's email address
        limit (int): Maximum number of conversations to return (default: 20)

    Returns:
        List[AISearchConversation]: List of user's conversations

    Raises:
        HTTPException: 500 if error occurs
    """
    try:
        ai_search_service = get_ai_search_service()
        conversations = ai_search_service.get_user_conversations(user_email, limit=limit)
        return conversations

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching user conversations: {str(e)}",
        )


# ==================== SEARCH HISTORY ENDPOINTS ====================


@router.get("/history/{user_email}", response_model=List[AISearchHistory])
async def get_search_history(
    user_email: str = Path(..., description="The user's email"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
):
    """
    Fetch search history for a user.

    Returns a simplified view of past questions and answers,
    suitable for displaying in a history list.

    Args:
        user_email (str): The user's email address
        limit (int): Maximum number of records to return (default: 20)

    Returns:
        List[AISearchHistory]: List of search history records

    Raises:
        HTTPException: 500 if error occurs
    """
    try:
        ai_search_service = get_ai_search_service()
        history = ai_search_service.get_search_history(user_email, limit=limit)
        return history

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching search history: {str(e)}",
        )


# ==================== HEALTH CHECK ENDPOINT ====================


@router.get("/health")
async def health_check():
    """
    Health check endpoint for AI Search service.

    Returns:
        dict: Service status and configuration
    """
    return {
        "status": "healthy",
        "service": "AI Search",
        "model": "gpt-4-turbo-preview",
        "temperature": 0.1,
    }
