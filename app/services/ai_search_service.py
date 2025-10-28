"""
AI Search Service

Provides AI-powered book search functionality using LangChain and ChatGPT-4.1.
Integrates with the book service to provide intelligent book recommendations.

Storage Structure:
- ai_search_questions/{user_email}/chat_history/{conversation_id}
"""

import json
import os
import tempfile
import time
from typing import List, Optional, Any, Dict
from datetime import datetime
from google.cloud.firestore import DocumentSnapshot, Increment, ArrayUnion
from dotenv import load_dotenv
from openai import OpenAI

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
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
from app.models.book import Book
from app.services.book_service import get_book_service
from app.utils.firebase_config import get_firestore_client


def load_env() -> None:
    """Load environment variables from .env file."""
    print("load_env");
    # os.
    load_dotenv()

load_env()

class AISearchService:
    """Service class for AI-powered search operations."""

    # New nested structure: ai_search_questions/{user_email}/chat_history/{conversation_id}
    USERS_COLLECTION = "ai_search_questions"  # Main collection for users
    CHAT_HISTORY_SUBCOLLECTION = "chat_history"  # Subcollection under each user

    FINE_TUNE_SYSTEM_PROMPT = (
        "You are an intelligent book recommendation assistant for the BookNest online bookstore. "
        "Recommend books that align with a reader's stated interests, explain your reasoning clearly, "
        "and highlight unique qualities of each title."
    )

    def __init__(self):
        """Initialize the AI search service."""
        self.db: Any = get_firestore_client()
        self.book_service = get_book_service()
        self.api_key = os.getenv("OPENAI_API_KEY")

        temperature_env = os.getenv("AI_SEARCH_MODEL_TEMPERATURE", "0.1")
        try:
            self.temperature = float(temperature_env)
        except (TypeError, ValueError):
            self.temperature = 0.1

        self.active_model_name = os.getenv("AI_SEARCH_MODEL", "gpt-4-turbo-preview")
        self.default_fine_tune_base_model = os.getenv(
            "AI_SEARCH_FINE_TUNE_BASE_MODEL", "gpt-4o-mini"
        )

        # Initialize ChatGPT-4.1 with LangChain
        # Temperature set to 0.1 for more deterministic responses
        self.llm = ChatOpenAI(
            model=self.active_model_name,
            temperature=self.temperature,
            openai_api_key=self.api_key,
        )

    # ==================== MODEL CONFIGURATION ====================

    def set_llm_model(self, model_name: str) -> None:
        """
        Update the active OpenAI model (base or fine-tuned) used for search responses.

        Args:
            model_name: The OpenAI model identifier to use.
        """
        if not model_name:
            raise ValueError("model_name must be provided when updating the AI model.")

        self.active_model_name = model_name
        self.llm = ChatOpenAI(
            model=self.active_model_name,
            temperature=self.temperature,
            api_key=self.api_key,
        )

    # ==================== FINE-TUNING SUPPORT ====================

    def _book_to_serializable(self, book: Book) -> Dict[str, Any]:
        """
        Convert a Book model into a JSON-serializable dictionary.

        Args:
            book: Book instance from Firestore

        Returns:
            Dictionary representation with ISO-formatted timestamps.
        """
        data = book.model_dump()

        for key, value in list(data.items()):
            if isinstance(value, datetime):
                data[key] = value.isoformat()

        data["id"] = book.id
        data["created_at"] = book.created_at.isoformat()
        data["updated_at"] = book.updated_at.isoformat()
        return data

    def fetch_books_as_dicts(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch books from Firestore and convert them into JSON-serializable dicts.

        Args:
            limit: Optional limit for number of books to fetch

        Returns:
            List of dictionaries representing books
        """
        books = self.book_service.get_all_books(limit=limit)
        return [self._book_to_serializable(book) for book in books]

    def export_books_json(self, limit: Optional[int] = None, *, indent: int = 2) -> str:
        """
        Export book documents to pretty-printed JSON string for inspection or backups.

        Args:
            limit: Optional limit for number of books to include
            indent: JSON indentation level

        Returns:
            JSON string containing the selected books
        """
        books_dicts = self.fetch_books_as_dicts(limit=limit)
        return json.dumps(books_dicts, indent=indent)

    def _build_fine_tune_user_prompt(self, book: Book) -> str:
        """
        Build a synthetic user message for fine-tuning based on book attributes.
        """
        prompt_parts: List[str] = ["I'm searching for a new book to read."]

        preferences: List[str] = []
        if book.genre:
            preferences.append(f"I enjoy {book.genre} books")
        if book.author:
            preferences.append(f"especially authors like {book.author}")
        if preferences:
            prompt_parts.append(" ".join(preferences) + ".")

        if book.price is not None:
            prompt_parts.append(f"My budget is about ${book.price:,.2f}.")

        prompt_parts.append("What would you recommend and why?")
        return " ".join(prompt_parts)

    def _build_fine_tune_assistant_response(self, book: Book) -> str:
        """
        Build the assistant reply used in fine-tuning examples.
        """
        title = book.title or "this book"
        author = book.author or "the author"

        response_parts: List[str] = [f'I recommend "{title}" by {author}.']

        if book.description:
            response_parts.append(book.description.strip())

        detail_fragments: List[str] = []
        if book.genre:
            detail_fragments.append(f"It belongs to the {book.genre} genre")
        if book.language:
            detail_fragments.append(f"Language: {book.language}")
        if book.price is not None:
            currency = book.currency or "USD"
            detail_fragments.append(f"Price: ${book.price:,.2f} {currency}")
        if book.rating is not None:
            detail_fragments.append(f"Average rating: {book.rating:.1f}/5")
        if book.page_count:
            detail_fragments.append(f"{book.page_count} pages")
        if book.publisher:
            detail_fragments.append(f"Published by {book.publisher}")
        if book.in_stock is not None:
            availability = "Currently in stock" if book.in_stock else "Currently out of stock"
            detail_fragments.append(availability)

        if detail_fragments:
            response_parts.append("Key details: " + "; ".join(detail_fragments) + ".")

        if book.is_new:
            response_parts.append("It's a fresh release that readers are excited about.")
        if book.is_featured:
            response_parts.append("This title is featured in our store because it resonates with many readers.")

        response_parts.append("Let me know if you'd like alternatives or a different style.")
        return " ".join(response_parts)

    def build_finetuning_dataset(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Build a chat-completions style dataset suitable for OpenAI fine-tuning.

        Args:
            limit: Optional limit for number of examples

        Returns:
            List of training examples in JSONL-compatible structure
        """
        books = self.book_service.get_all_books(limit=limit)

        dataset: List[Dict[str, Any]] = []
        for book in books:
            dataset.append(
                {
                    "messages": [
                        {"role": "system", "content": self.FINE_TUNE_SYSTEM_PROMPT},
                        {"role": "user", "content": self._build_fine_tune_user_prompt(book)},
                        {
                            "role": "assistant",
                            "content": self._build_fine_tune_assistant_response(book),
                        },
                    ]
                }
            )

        return dataset

    def start_books_fine_tuning(
        self,
        *,
        limit: Optional[int] = None,
        base_model: Optional[str] = None,
        suffix: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Prepare book data, upload it as JSONL, and launch an OpenAI fine-tuning job.

        Args:
            limit: Optional limit for number of book examples to include
            base_model: Base model to fine-tune (defaults to env or gpt-4o-mini)
            suffix: Optional suffix for the resulting fine-tuned model name
            dry_run: If True, skip upload and return dataset preview only

        Returns:
            Dict with details about the prepared dataset and fine-tuning job
        """
        dataset = self.build_finetuning_dataset(limit=limit)

        if not dataset:
            raise ValueError("No books available to build a fine-tuning dataset.")

        jsonl_payload = "\n".join(json.dumps(record, ensure_ascii=False) for record in dataset)

        if dry_run:
            return {
                "training_records": len(dataset),
                "jsonl_preview": jsonl_payload.splitlines()[:5],
            }

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required to start fine-tuning.")

        client = OpenAI(api_key=self.api_key)
        training_file = None
        fine_tune_job = None
        tmp_path: Optional[str] = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w+",
                encoding="utf-8",
                suffix=".jsonl",
                delete=False,
            ) as tmp_file:
                tmp_file.write(jsonl_payload)
                tmp_file.flush()
                tmp_path = tmp_file.name

            if not tmp_path:
                raise RuntimeError("Failed to create temporary dataset file for fine-tuning.")

            with open(tmp_path, "rb") as file_handle:
                training_file = client.files.create(file=file_handle, purpose="fine-tune")

            fine_tune_job = client.fine_tuning.jobs.create(
                training_file=training_file.id,
                model=base_model or self.default_fine_tune_base_model,
                suffix=suffix or "ai-search-books",
            )

            result: Dict[str, Any] = {
                "training_records": len(dataset),
                "file_id": training_file.id,
                "fine_tune_job_id": fine_tune_job.id,
                "base_model": fine_tune_job.model,
                "status": fine_tune_job.status,
            }

            fine_tuned_model = getattr(fine_tune_job, "fine_tuned_model", None)
            if fine_tuned_model:
                result["fine_tuned_model"] = fine_tuned_model

            return result
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    # ==================== HELPER METHODS FOR PATH ====================

    def _get_user_doc_ref(self, user_email: str):
        """Get reference to user document."""
        return self.db.collection(self.USERS_COLLECTION).document(user_email)

    def _get_chat_history_collection_ref(self, user_email: str):
        """Get reference to chat_history subcollection for a user."""
        return self._get_user_doc_ref(user_email).collection(self.CHAT_HISTORY_SUBCOLLECTION)

    def _get_conversation_doc_ref(self, user_email: str, conversation_id: str):
        """Get reference to a specific conversation document."""
        return self._get_chat_history_collection_ref(user_email).document(conversation_id)

    def _recompute_user_conversation_stats(self, user_email: str) -> None:
        """
        Recalculate and update user's conversation metadata.

        Args:
            user_email: User's email address
        """
        try:
            chat_history_ref = self._get_chat_history_collection_ref(user_email)
            conversations = list(chat_history_ref.stream())
            conversation_count = len(conversations)

            user_doc_ref = self._get_user_doc_ref(user_email)
            user_doc = user_doc_ref.get()

            if conversation_count == 0:
                if user_doc.exists:
                    user_doc_ref.delete()
                return

            if not user_doc.exists:
                self._ensure_user_document_exists(user_email)

            user_doc_ref.update({
                "total_conversations": conversation_count,
                "last_activity": datetime.now(),
            })
        except Exception as e:
            raise Exception(f"Error recomputing user conversation stats: {str(e)}")

    # ==================== USER DOCUMENT OPERATIONS ====================

    def _ensure_user_document_exists(self, user_email: str) -> None:
        """
        Ensure user document exists in the main collection.
        Creates it if it doesn't exist.

        Args:
            user_email: User's email address
        """
        try:
            user_doc_ref = self._get_user_doc_ref(user_email)
            user_doc = user_doc_ref.get()

            if not user_doc.exists:
                # Create user document with metadata
                user_doc_ref.set({
                    "user_email": user_email,
                    "created_at": datetime.now(),
                    "last_activity": datetime.now(),
                    "total_conversations": 0,
                })
        except Exception as e:
            raise Exception(f"Error ensuring user document exists: {str(e)}")

    def _update_user_activity(self, user_email: str) -> None:
        """
        Update user's last activity timestamp.

        Args:
            user_email: User's email address
        """
        try:
            user_doc_ref = self._get_user_doc_ref(user_email)
            user_doc_ref.update({
                "last_activity": datetime.now()
            })
        except Exception as e:
            # If update fails, it might mean the document doesn't exist
            self._ensure_user_document_exists(user_email)

    # ==================== CONVERSATION OPERATIONS ====================

    def create_conversation(
        self, user_email: str, title: str, initial_question: str
    ) -> AISearchConversation:
        """
        Create a new conversation in the user's chat history.

        Args:
            user_email: User's email address
            title: Conversation title
            initial_question: First question in the conversation

        Returns:
            AISearchConversation: The created conversation

        Raises:
            Exception: If there's an error creating the conversation
        """
        try:
            # Ensure user document exists
            self._ensure_user_document_exists(user_email)

            now = datetime.now()

            # Create conversation data
            conversation_data = {
                "user_email": user_email,
                "title": title,
                "created_at": now,
                "updated_at": now,
                "messages": [],
                "question": initial_question,
                "answer": "",  # Will be filled when AI responds
                "recommended_books": [],
                "suggestions": [],
            }

            # Create conversation document in subcollection
            chat_history_ref = self._get_chat_history_collection_ref(user_email)
            doc_ref = chat_history_ref.document()
            doc_ref.set(conversation_data)

            # Update user's conversation count
            user_doc_ref = self._get_user_doc_ref(user_email)
            user_doc_ref.update({
                "total_conversations": Increment(1),
                "last_activity": now,
            })

            return AISearchConversation(
                id=doc_ref.id,
                user_email=user_email,
                title=title,
                created_at=now,
                updated_at=now,
                messages=[],
            )
        except Exception as e:
            raise Exception(f"Error creating conversation: {str(e)}")

    def get_conversation_by_id(
        self, user_email: str, conversation_id: str
    ) -> Optional[AISearchConversation]:
        """
        Fetch a conversation by its ID.

        Args:
            user_email: User's email address
            conversation_id: The conversation ID

        Returns:
            Optional[AISearchConversation]: Conversation if found, None otherwise
        """
        try:
            doc = self._get_conversation_doc_ref(user_email, conversation_id).get()

            if doc.exists:
                return self._document_to_conversation(doc)
            else:
                return None
        except Exception as e:
            raise Exception(f"Error fetching conversation: {str(e)}")

    def get_user_conversations(
        self, user_email: str, limit: int = 20
    ) -> List[AISearchConversation]:
        """
        Fetch all conversations for a user.

        Args:
            user_email: User's email address
            limit: Maximum number of conversations to return

        Returns:
            List[AISearchConversation]: List of user's conversations
        """
        try:
            docs = (
                self._get_chat_history_collection_ref(user_email)
                .order_by("updated_at", direction="DESCENDING")
                .limit(limit)
                .stream()
            )
            return [self._document_to_conversation(doc) for doc in docs]
        except Exception as e:
            raise Exception(f"Error fetching user conversations: {str(e)}")

    def update_conversation(
        self,
        user_email: str,
        conversation_id: str,
        answer: str,
        recommended_books: List[RecommendedBook],
        suggestions: List[str],
    ) -> None:
        """
        Update conversation with AI response data.

        Args:
            user_email: User's email address
            conversation_id: The conversation ID
            answer: AI-generated answer
            recommended_books: List of recommended books
            suggestions: List of follow-up suggestions
        """
        try:
            doc_ref = self._get_conversation_doc_ref(user_email, conversation_id)
            doc_ref.update({
                "answer": answer,
                "recommended_books": [book.model_dump() for book in recommended_books],
                "suggestions": suggestions,
                "updated_at": datetime.now(),
            })

            # Update user activity
            self._update_user_activity(user_email)
        except Exception as e:
            raise Exception(f"Error updating conversation: {str(e)}")

    def add_message_to_conversation(
        self,
        user_email: str,
        conversation_id: str,
        role: str,
        content: str,
        book_references: Optional[List[str]] = None,
    ) -> None:
        """
        Add a message to a conversation.

        Args:
            user_email: User's email address
            conversation_id: The conversation ID
            role: Message role ('user' or 'assistant')
            content: Message content
            book_references: Optional list of referenced book IDs
        """
        try:
            doc_ref = self._get_conversation_doc_ref(user_email, conversation_id)

            message = {
                "id": self.db.collection("_temp").document().id,  # Generate unique ID
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "timestamp": datetime.now(),
                "book_references": book_references or [],
            }

            doc_ref.update({
                "messages": ArrayUnion([message]),
                "updated_at": datetime.now(),
            })

            # Update user activity
            self._update_user_activity(user_email)
        except Exception as e:
            raise Exception(f"Error adding message to conversation: {str(e)}")

    def delete_conversation(
        self, user_email: str, conversation_id: str
    ) -> bool:
        """
        Delete a specific conversation from user's chat history.

        Args:
            user_email: User's email address
            conversation_id: The conversation ID to delete

        Returns:
            bool: True if deleted successfully, False if not found

        Raises:
            Exception: If there's an error deleting the conversation
        """
        try:
            doc_ref = self._get_conversation_doc_ref(user_email, conversation_id)
            doc = doc_ref.get()

            if not doc.exists:
                return False

            # Delete the conversation document
            doc_ref.delete()

            # Recompute user stats to avoid negative counters
            self._recompute_user_conversation_stats(user_email)

            return True
        except Exception as e:
            raise Exception(f"Error deleting conversation: {str(e)}")

    def delete_all_conversations(self, user_email: str) -> int:
        """
        Delete all conversations for a user (clear chat history).

        Args:
            user_email: User's email address

        Returns:
            int: Number of conversations deleted

        Raises:
            Exception: If there's an error deleting conversations
        """
        try:
            # Get all conversations for the user
            chat_history_ref = self._get_chat_history_collection_ref(user_email)
            docs = list(chat_history_ref.stream())

            deleted_count = 0
            for doc in docs:
                doc.reference.delete()
                deleted_count += 1

            user_doc_ref = self._get_user_doc_ref(user_email)

            if deleted_count > 0:
                # Delete the user chat history document after removing conversations
                user_doc_ref.delete()
            else:
                # Ensure empty user document is removed if it exists without conversations
                if user_doc_ref.get().exists:
                    user_doc_ref.delete()

            return deleted_count
        except Exception as e:
            raise Exception(f"Error deleting all conversations: {str(e)}")

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
            conversation_id: Optional conversation ID for continuing conversation

        Returns:
            Dict containing question_id, answer_id, answer, recommended_books, and suggestions

        Raises:
            Exception: If there's an error during AI search
        """
        try:
            start_time = time.time()

            # Get conversation history if continuing a conversation
            conversation_history = []
            if conversation_id:
                conversation = self.get_conversation_by_id(user_email, conversation_id)
                if conversation:
                    conversation_history = conversation.messages[-5:]  # Last 5 messages

            # Create or get conversation
            if conversation_id:
                # Continuing existing conversation
                conv_id = conversation_id
                title = None  # Don't update title for existing conversation
            else:
                # Create new conversation
                title = question[:100]  # Use first 100 chars as title
                conversation = self.create_conversation(user_email, title, question)
                conv_id = conversation.id

            # Add user message to conversation
            self.add_message_to_conversation(
                user_email=user_email,
                conversation_id=conv_id,
                role="user",
                content=question,
            )

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

            # Add assistant message to conversation
            self.add_message_to_conversation(
                user_email=user_email,
                conversation_id=conv_id,
                role="assistant",
                content=ai_response,
                book_references=[book.book_id for book in recommended_books],
            )

            # Update conversation with answer and recommendations
            self.update_conversation(
                user_email=user_email,
                conversation_id=conv_id,
                answer=ai_response,
                recommended_books=recommended_books,
                suggestions=suggestions,
            )

            return {
                "question_id": conv_id,  # Using conversation_id as question_id
                "answer_id": conv_id,  # Using conversation_id as answer_id
                "answer": ai_response,
                "recommended_books": recommended_books,
                "suggestions": suggestions,
                "conversation_id": conv_id,
            }

        except Exception as e:
            raise Exception(f"Error performing AI search: {str(e)}")

    async def _get_books_context(
        self, context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
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
            # Format books catalog
            books_catalog = "\n".join(
                [
                    f"- {book['title']} by {book['author']} ({book['genre']}) - ${book['price']}"
                    + (f" - Rating: {book['rating']}/5" if book.get("rating") else "")
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
            history_messages: List[BaseMessage] = []
            for msg in conversation_history:
                if msg.role == "user":
                    history_messages.append(HumanMessage(content=msg.content))
                else:
                    history_messages.append(AIMessage(content=msg.content))

            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", SYSTEM_PROMPT_TEMPLATE),
                    MessagesPlaceholder("history"),
                    ("human", "{question}"),
                ]
            ).partial(
                books_catalog=books_catalog or "No books currently available",
                context_info=context_info or "No specific filters applied",
            )

            chain = prompt | self.llm
            response = await chain.ainvoke({"history": history_messages, "question": question})

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
                if book["title"].lower() in ai_response.lower():
                    relevance_score = 0.95
                elif book["author"].lower() in ai_response.lower():
                    relevance_score = 0.85

                # Increase score based on rating
                if book.get("rating"):
                    relevance_score += book["rating"] / 10  # Add up to 0.5

                # Cap at 1.0
                relevance_score = min(relevance_score, 1.0)

                reason = f"Based on your interest in {book['genre']} books"
                if book.get("rating") and book["rating"] >= 4.0:
                    reason += f" and its high rating of {book['rating']}/5"

                recommended.append(
                    RecommendedBook(
                        book_id=book["id"],
                        title=book["title"],
                        author=book["author"],
                        relevance_score=round(relevance_score, 2),
                        reason=reason,
                        price=book["price"],
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
            # Fetch conversations from user's chat history
            docs = (
                self._get_chat_history_collection_ref(user_email)
                .order_by("created_at", direction="DESCENDING")
                .limit(limit)
                .stream()
            )

            history = []
            for doc in docs:
                data = doc.to_dict()
                history.append(
                    AISearchHistory(
                        id=doc.id,
                        question=data.get("question", ""),
                        answer=data.get("answer", ""),
                        user_email=user_email,
                        created_at=data.get("created_at"),
                        book_recommendations=len(data.get("recommended_books", [])),
                    )
                )

            return history
        except Exception as e:
            raise Exception(f"Error fetching search history: {str(e)}")

    # ==================== BACKWARDS COMPATIBILITY METHODS ====================
    # These methods maintain API compatibility with the old structure

    def get_question_by_id(self, question_id: str) -> Optional[AISearchQuestion]:
        """
        Fetch a question by its ID (conversation ID).

        Note: In the new structure, question_id is the same as conversation_id.
        We need user_email to fetch it, so this method searches across users.
        """
        try:
            # This is less efficient but maintains backwards compatibility
            # In practice, you should use get_conversation_by_id with user_email
            users_docs = self.db.collection(self.USERS_COLLECTION).stream()

            for user_doc in users_docs:
                conv_doc = (
                    user_doc.reference
                    .collection(self.CHAT_HISTORY_SUBCOLLECTION)
                    .document(question_id)
                    .get()
                )

                if conv_doc.exists:
                    data = conv_doc.to_dict()
                    return AISearchQuestion(
                        id=conv_doc.id,
                        question=data.get("question", ""),
                        user_email=data.get("user_email"),
                        created_at=data.get("created_at"),
                        search_context=data.get("search_context"),
                        ai_model_config=data.get("ai_model_config"),
                    )

            return None
        except Exception as e:
            raise Exception(f"Error fetching question: {str(e)}")

    def get_answer_by_id(self, answer_id: str) -> Optional[AISearchAnswer]:
        """
        Fetch an answer by its ID (conversation ID).

        Note: In the new structure, answer_id is the same as conversation_id.
        """
        try:
            # This is less efficient but maintains backwards compatibility
            users_docs = self.db.collection(self.USERS_COLLECTION).stream()

            for user_doc in users_docs:
                conv_doc = (
                    user_doc.reference
                    .collection(self.CHAT_HISTORY_SUBCOLLECTION)
                    .document(answer_id)
                    .get()
                )

                if conv_doc.exists:
                    data = conv_doc.to_dict()

                    # Convert recommended_books dicts back to RecommendedBook objects
                    recommended_books = []
                    for book_data in data.get("recommended_books", []):
                        if isinstance(book_data, dict):
                            recommended_books.append(RecommendedBook(**book_data))

                    return AISearchAnswer(
                        id=conv_doc.id,
                        question_id=conv_doc.id,
                        answer=data.get("answer", ""),
                        user_email=data.get("user_email"),
                        created_at=data.get("created_at"),
                        recommended_books=recommended_books,
                        suggestions=data.get("suggestions", []),
                        model_metadata=data.get("model_metadata"),
                        sources=data.get("sources"),
                    )

            return None
        except Exception as e:
            raise Exception(f"Error fetching answer: {str(e)}")

    def get_answers_for_question(self, question_id: str) -> List[AISearchAnswer]:
        """
        Fetch all answers for a specific question.

        Note: In the new structure, each conversation has one answer.
        """
        try:
            answer = self.get_answer_by_id(question_id)
            return [answer] if answer else []
        except Exception as e:
            raise Exception(f"Error fetching answers: {str(e)}")

    # ==================== HELPER METHODS ====================

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
SYSTEM_PROMPT_TEMPLATE = """You are an intelligent book recommendation assistant for an online bookstore.
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
