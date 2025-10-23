# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from app.utils.firebase_config import init_firebase
from app.services.member_service import get_member_service


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Handle application startup and shutdown events."""
    # Startup
    try:
        init_firebase()
        print("✓ Application startup: Firebase initialized successfully")
    except Exception as e:
        print(f"✗ Application startup error: {str(e)}")
        raise
    yield
    # Shutdown
    print("✓ Application shutdown")


app = FastAPI(title="Mini Online Bookstore Backend", version="1.0.0", lifespan=lifespan)


@app.get("/")
def read_root():
    return {"message": "Welcome to Mini Online Bookstore Backend API", "version": "1.0.0"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}


@app.get("/members/{member_id}")
async def get_member(member_id: str):
    """
    Fetch a member from the members collection by ID.

    Args:
        member_id (str): The member's document ID in Firestore

    Returns:
        dict: Member data if found

    Raises:
        HTTPException: 404 if member not found, 500 if database error occurs
    """
    try:
        member_service = get_member_service()
        member = member_service.fetch_user_by_id(member_id)

        if member is None:
            raise HTTPException(status_code=404, detail=f"Member with ID '{member_id}' not found")

        return member.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/members/email/{email}")
async def get_member_by_email(email: str):
    """
    Fetch a member from the members collection by email address.

    Args:
        email (str): The member's email address

    Returns:
        dict: Member data if found

    Raises:
        HTTPException: 404 if member not found, 500 if database error occurs
    """
    try:
        member_service = get_member_service()
        member = member_service.fetch_user_by_email(email)

        if member is None:
            raise HTTPException(status_code=404, detail=f"Member with email '{email}' not found")

        return member.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/members")
async def get_all_members():
    """
    Fetch all members from the members collection.

    Returns:
        list: List of all member data

    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        member_service = get_member_service()
        members = member_service.fetch_all_users()
        return [member.model_dump() for member in members]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")