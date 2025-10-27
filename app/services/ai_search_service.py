"""
AI Search Service

Provides AI-powered book search functionality using LangChain and ChatGPT-4.1.
Integrates with the book service to provide intelligent book recommendations.
"""

import os
import time
from typing import List, Optional, Any, Dict
from datetime import datetime
from google.cloud.firestore import DocumentSnapshot

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.models.ai_search import (
    AISearchQuestion,
    AISearchQuestionCreate,
    AISearchAnswer,
    AISearchAnswerCreate,
    AISearchConversation,
    AISearchConversationCreate,
    AISearchMessage,
    AISearchHistory,
    RecommendedBook,
    ModelMetadata,
    SourceInfo,
)
from app.services.book_service import get_book_service
from app.utils.firebase_config import get_firestore_client


class AISearchService:
    """Service class for AI-powered search operations."""

    QUESTIONS_COLLECTION = "ai_search_questions"
    ANSWERS_COLLECTION = "ai_search_answers"
    CONVERSATIONS_COLLECTION = "ai_search_conversations"

    def __init__(self):
        """Initialize the AI search service."""
        self.db: Any = get_firestore_client()
        self.book_service = get_book_service()

        # Initialize ChatGPT-4.1 with LangChain
        # Temperature set to 0.1 for more deterministic responses
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",  # Using GPT-4 Turbo
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

    # ==================== QUESTION OPERATIONS ====================

    def create_question(self, question_data: AISearchQuestionCreate) -> AISearchQuestion:
        """
        Create a new AI search question.

        Args:
            question_data: The question data to create

        Returns:
            AISearchQuestion: The created question with ID

        Raises:
            Exception: If there's an error creating the question
        """
        try:
            now = datetime.now()
            data = {
                **question_data.model_dump(exclude_none=True),
                "created_at": now,
            }

            doc_ref = self.db.collection(self.QUESTIONS_COLLECTION).document()
            doc_ref.set(data)

            return AISearchQuestion(
                id=doc_ref.id,
                created_at=now,
                **question_data.model_dump(),
            )
        except Exception as e:
            raise Exception(f"Error creating question: {str(e)}")

    def get_question_by_id(self, question_id: str) -> Optional[AISearchQuestion]:
        """
        Fetch a question by its ID.

        Args:
            question_id: The unique identifier of the question

        Returns:
            Optional[AISearchQuestion]: Question object if found, None otherwise
        """
        try:
            doc = self.db.collection(self.QUESTIONS_COLLECTION).document(question_id).get()

            if doc.exists:
                return self._document_to_question(doc)
            else:
                return None
        except Exception as e:
            raise Exception(f"Error fetching question: {str(e)}")

    # ==================== ANSWER OPERATIONS ====================

    def create_answer(self, answer_data: AISearchAnswerCreate) -> AISearchAnswer:
        """
        Create a new AI search answer.

        Args:
            answer_data: The answer data to create

        Returns:
            AISearchAnswer: The created answer with ID

        Raises:
            Exception: If there's an error creating the answer
        """
        try:
            now = datetime.now()
            data = {
                **answer_data.model_dump(exclude_none=True),
                "created_at": now,
            }

            doc_ref = self.db.collection(self.ANSWERS_COLLECTION).document()
            doc_ref.set(data)

            return AISearchAnswer(
                id=doc_ref.id,
                created_at=now,
                **answer_data.model_dump(),
            )
        except Exception as e:
            raise Exception(f"Error creating answer: {str(e)}")

    def get_answer_by_id(self, answer_id: str) -> Optional[AISearchAnswer]:
        """
        Fetch an answer by its ID.

        Args:
            answer_id: The unique identifier of the answer

        Returns:
            Optional[AISearchAnswer]: Answer object if found, None otherwise
        """
        try:
            doc = self.db.collection(self.ANSWERS_COLLECTION).document(answer_id).get()

            if doc.exists:
                return self._document_to_answer(doc)
            else:
                return None
        except Exception as e:
            raise Exception(f"Error fetching answer: {str(e)}")

    def get_answers_for_question(self, question_id: str) -> List[AISearchAnswer]:
        """
        Fetch all answers for a specific question.

        Args:
            question_id: The question ID

        Returns:
            List[AISearchAnswer]: List of answers
        """
        try:
            docs = (
                self.db.collection(self.ANSWERS_COLLECTION)
                .where("question_id", "==", question_id)
                .stream()
            )
            return [self._document_to_answer(doc) for doc in docs]
        except Exception as e:
            raise Exception(f"Error fetching answers: {str(e)}")

    # ==================== AI SEARCH OPERATIONS ====================

    async def search_with_ai(
        self,
        question: str,
        user_email: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform AI-powered book search using LangChain.

        Args:
            question: The user's question
            user_email: The user's email
            context: Optional search context (genre, price range, filters)
            conversation_id: Optional conversation ID for context

        Returns:
            Dict containing question_id, answer_id, answer, recommended_books, and suggestions

        Raises:
            Exception: If there's an error during AI search
        """
        try:
            start_time = time.time()

            # Create question record
            question_data = AISearchQuestionCreate(
                question=question,
                user_email=user_email,
                search_context=context,
            )
            created_question = self.create_question(question_data)

            # Get conversation history if continuing a conversation
            conversation_history = []
            if conversation_id:
                conversation = self.get_conversation_by_id(conversation_id)
                if conversation:
                    conversation_history = conversation.messages[-5:]  # Last 5 messages

            # Fetch relevant books from database
            books_context = await self._get_books_context(context)

            # Generate AI response using LangChain
            ai_response = await self._generate_ai_response(
                question=question,
                books_context=books_context,
                conversation_history=conversation_history,
                context=context,
            )

            # Recommend books based on AI analysis
            recommended_books = self._recommend_books(
                question=question,
                ai_response=ai_response,
                books_context=books_context,
            )

            # Generate follow-up suggestions
            suggestions = self._generate_suggestions(question, ai_response)

            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)

            # Create metadata
            metadata = ModelMetadata(
                model="gpt-4-turbo-preview",
                tokens_used=0,  # OpenAI API doesn't always return token count in streaming
                confidence=0.85,  # Default confidence score
                processing_time=processing_time,
            )

            # Create answer record
            answer_data = AISearchAnswerCreate(
                question_id=created_question.id,
                answer=ai_response,
                user_email=user_email,
                recommended_books=recommended_books,
                suggestions=suggestions,
                model_metadata=metadata,
            )
            created_answer = self.create_answer(answer_data)

            # Update or create conversation
            if conversation_id:
                self._add_message_to_conversation(
                    conversation_id=conversation_id,
                    role="user",
                    content=question,
                )
                self._add_message_to_conversation(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=ai_response,
                    book_references=[book.book_id for book in recommended_books],
                )
            else:
                # Create new conversation
                conversation_data = AISearchConversationCreate(
                    user_email=user_email,
                    title=question[:100],  # Use first 100 chars as title
                )
                conversation = self.create_conversation(conversation_data)
                conversation_id = conversation.id

                # Add messages
                self._add_message_to_conversation(
                    conversation_id=conversation_id,
                    role="user",
                    content=question,
                )
                self._add_message_to_conversation(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=ai_response,
                    book_references=[book.book_id for book in recommended_books],
                )

            return {
                "question_id": created_question.id,
                "answer_id": created_answer.id,
                "answer": ai_response,
                "recommended_books": recommended_books,
                "suggestions": suggestions,
                "conversation_id": conversation_id,
            }

        except Exception as e:
            raise Exception(f"Error performing AI search: {str(e)}")

    async def _get_books_context(self, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Fetch relevant books from the database based on context.

        Args:
            context: Search context with filters

        Returns:
            List of book data dictionaries
        """
        try:
            # Get all books or filtered books
            if context and (context.get("genre") or context.get("price_range")):
                # Apply filters if provided
                books = self.book_service.get_all_books(limit=50)
            else:
                # Get featured or popular books
                books = self.book_service.get_featured_books(limit=20)

            return [
                {
                    "id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "genre": book.genre,
                    "description": book.description,
                    "price": book.price,
                    "rating": book.rating,
                    "in_stock": book.in_stock,
                }
                for book in books
            ]
        except Exception as e:
            print(f"Warning: Error fetching books context: {str(e)}")
            return []

    async def _generate_ai_response(
        self,
        question: str,
        books_context: List[Dict[str, Any]],
        conversation_history: List[AISearchMessage],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate AI response using LangChain and ChatGPT-4.1.

        Args:
            question: User's question
            books_context: Available books information
            conversation_history: Previous conversation messages
            context: Additional context

        Returns:
            str: AI-generated response
        """
        try:
            # Build system prompt
            system_prompt = """You are an intelligent book recommendation assistant for an online bookstore.
Your role is to help users find the perfect books based on their questions and preferences.

Guidelines:
1. Provide thoughtful, personalized recommendations
2. Consider the user's reading preferences, genre interests, and budget
3. Explain why you recommend specific books
4. Be conversational and friendly
5. If you don't have enough information, ask clarifying questions
6. Reference specific books from the available catalog when possible

Available books in our catalog:
{books_catalog}

Context filters:
{context_info}
"""

            # Format books catalog
            books_catalog = "\n".join(
                [
                    f"- {book['title']} by {book['author']} ({book['genre']}) - ${book['price']}"
                    + (f" - Rating: {book['rating']}/5" if book.get('rating') else "")
                    for book in books_context[:10]  # Show top 10 books
                ]
            )

            # Format context info
            context_info = ""
            if context:
                if context.get("genre"):
                    context_info += f"Genre preference: {context['genre']}\n"
                if context.get("price_range"):
                    pr = context["price_range"]
                    context_info += f"Price range: ${pr.get('min', 0)} - ${pr.get('max', 'unlimited')}\n"

            # Build conversation history for context
            messages = [
                SystemMessage(content=system_prompt.format(
                    books_catalog=books_catalog or "No books currently available",
                    context_info=context_info or "No specific filters applied"
                ))
            ]

            # Add conversation history
            for msg in conversation_history:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                else:
                    messages.append(AIMessage(content=msg.content))

            # Add current question
            messages.append(HumanMessage(content=question))

            # Get AI response
            response = self.llm.invoke(messages)

            return response.content

        except Exception as e:
            raise Exception(f"Error generating AI response: {str(e)}")

    def _recommend_books(
        self,
        question: str,
        ai_response: str,
        books_context: List[Dict[str, Any]],
    ) -> List[RecommendedBook]:
        """
        Extract and recommend books based on the AI response and available books.

        Args:
            question: Original user question
            ai_response: AI-generated response
            books_context: Available books

        Returns:
            List[RecommendedBook]: List of recommended books with relevance scores
        """
        try:
            recommended = []

            # Simple keyword matching for now
            # In production, you might use embeddings or more sophisticated matching
            question_lower = question.lower()

            for book in books_context[:5]:  # Top 5 recommendations
                # Calculate simple relevance score
                relevance_score = 0.5  # Base score

                # Increase score if book is mentioned in response
                if book['title'].lower() in ai_response.lower():
                    relevance_score = 0.95
                elif book['author'].lower() in ai_response.lower():
                    relevance_score = 0.85

                # Increase score based on rating
                if book.get('rating'):
                    relevance_score += (book['rating'] / 10)  # Add up to 0.5

                # Cap at 1.0
                relevance_score = min(relevance_score, 1.0)

                reason = f"Based on your interest in {book['genre']} books"
                if book.get('rating') and book['rating'] >= 4.0:
                    reason += f" and its high rating of {book['rating']}/5"

                recommended.append(
                    RecommendedBook(
                        book_id=book['id'],
                        title=book['title'],
                        author=book['author'],
                        relevance_score=round(relevance_score, 2),
                        reason=reason,
                        price=book['price'],
                    )
                )

            # Sort by relevance score
            recommended.sort(key=lambda x: x.relevance_score, reverse=True)

            return recommended[:3]  # Return top 3

        except Exception as e:
            print(f"Warning: Error recommending books: {str(e)}")
            return []

    def _generate_suggestions(self, question: str, ai_response: str) -> List[str]:
        """
        Generate follow-up suggestions for the user.

        Args:
            question: Original question
            ai_response: AI response

        Returns:
            List[str]: List of suggested follow-up questions
        """
        suggestions = [
            "Can you recommend similar books in a different genre?",
            "What are the bestsellers in this category?",
            "Do you have books by the same author?",
        ]

        return suggestions[:3]

    # ==================== CONVERSATION OPERATIONS ====================

    def create_conversation(
        self, conversation_data: AISearchConversationCreate
    ) -> AISearchConversation:
        """Create a new conversation."""
        try:
            now = datetime.now()
            data = {
                **conversation_data.model_dump(),
                "created_at": now,
                "updated_at": now,
                "messages": [],
            }

            doc_ref = self.db.collection(self.CONVERSATIONS_COLLECTION).document()
            doc_ref.set(data)

            return AISearchConversation(
                id=doc_ref.id,
                created_at=now,
                updated_at=now,
                messages=[],
                **conversation_data.model_dump(),
            )
        except Exception as e:
            raise Exception(f"Error creating conversation: {str(e)}")

    def get_conversation_by_id(self, conversation_id: str) -> Optional[AISearchConversation]:
        """Fetch a conversation by its ID."""
        try:
            doc = (
                self.db.collection(self.CONVERSATIONS_COLLECTION)
                .document(conversation_id)
                .get()
            )

            if doc.exists:
                return self._document_to_conversation(doc)
            else:
                return None
        except Exception as e:
            raise Exception(f"Error fetching conversation: {str(e)}")

    def get_user_conversations(self, user_email: str, limit: int = 20) -> List[AISearchConversation]:
        """Fetch all conversations for a user."""
        try:
            docs = (
                self.db.collection(self.CONVERSATIONS_COLLECTION)
                .where("user_email", "==", user_email)
                .order_by("updated_at", direction="DESCENDING")
                .limit(limit)
                .stream()
            )
            return [self._document_to_conversation(doc) for doc in docs]
        except Exception as e:
            raise Exception(f"Error fetching user conversations: {str(e)}")

    def _add_message_to_conversation(
        self,
        conversation_id: str,
        role: str,
        content: str,
        book_references: Optional[List[str]] = None,
    ) -> None:
        """Add a message to a conversation."""
        try:
            doc_ref = self.db.collection(self.CONVERSATIONS_COLLECTION).document(conversation_id)

            message = {
                "id": self.db.collection("_temp").document().id,  # Generate unique ID
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "timestamp": datetime.now(),
                "book_references": book_references or [],
            }

            doc_ref.update({
                "messages": self.db.field_value.array_union([message]),
                "updated_at": datetime.now(),
            })
        except Exception as e:
            raise Exception(f"Error adding message to conversation: {str(e)}")

    # ==================== SEARCH HISTORY ====================

    def get_search_history(
        self, user_email: str, limit: int = 20
    ) -> List[AISearchHistory]:
        """
        Get search history for a user.

        Args:
            user_email: User's email
            limit: Maximum number of records

        Returns:
            List[AISearchHistory]: Search history
        """
        try:
            # Fetch questions
            question_docs = (
                self.db.collection(self.QUESTIONS_COLLECTION)
                .where("user_email", "==", user_email)
                .order_by("created_at", direction="DESCENDING")
                .limit(limit)
                .stream()
            )

            history = []
            for q_doc in question_docs:
                question = self._document_to_question(q_doc)

                # Fetch corresponding answer
                answers = self.get_answers_for_question(question.id)
                if answers:
                    answer = answers[0]
                    history.append(
                        AISearchHistory(
                            id=question.id,
                            question=question.question,
                            answer=answer.answer,
                            user_email=user_email,
                            created_at=question.created_at,
                            book_recommendations=len(answer.recommended_books or []),
                        )
                    )

            return history
        except Exception as e:
            raise Exception(f"Error fetching search history: {str(e)}")

    # ==================== HELPER METHODS ====================

    @staticmethod
    def _document_to_question(doc: DocumentSnapshot) -> AISearchQuestion:
        """Convert Firestore document to AISearchQuestion."""
        data = doc.to_dict()
        return AISearchQuestion(
            id=doc.id,
            question=data.get("question"),
            user_email=data.get("user_email"),
            created_at=data.get("created_at"),
            search_context=data.get("search_context"),
            ai_model_config=data.get("ai_model_config"),
        )

    @staticmethod
    def _document_to_answer(doc: DocumentSnapshot) -> AISearchAnswer:
        """Convert Firestore document to AISearchAnswer."""
        data = doc.to_dict()
        return AISearchAnswer(
            id=doc.id,
            question_id=data.get("question_id"),
            answer=data.get("answer"),
            user_email=data.get("user_email"),
            created_at=data.get("created_at"),
            recommended_books=data.get("recommended_books"),
            suggestions=data.get("suggestions"),
            model_metadata=data.get("model_metadata"),
            sources=data.get("sources"),
        )

    @staticmethod
    def _document_to_conversation(doc: DocumentSnapshot) -> AISearchConversation:
        """Convert Firestore document to AISearchConversation."""
        data = doc.to_dict()

        # Convert message dicts to AISearchMessage objects
        messages = []
        for msg_data in data.get("messages", []):
            messages.append(
                AISearchMessage(
                    id=msg_data.get("id"),
                    conversation_id=msg_data.get("conversation_id"),
                    role=msg_data.get("role"),
                    content=msg_data.get("content"),
                    timestamp=msg_data.get("timestamp"),
                    book_references=msg_data.get("book_references"),
                )
            )

        return AISearchConversation(
            id=doc.id,
            user_email=data.get("user_email"),
            title=data.get("title"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            messages=messages,
        )


# Convenience function to create a service instance
def get_ai_search_service() -> AISearchService:
    """Create and return an AI search service instance."""
    return AISearchService()
