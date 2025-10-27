# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.utils.firebase_config import init_firebase
from app.routers import websocket, cart, books, auth, member, advertisements, payments, like, ai_search
from fastapi.middleware.cors import CORSMiddleware

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

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # 배포 도메인도 여기에 추가
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          
    allow_credentials=True,         
    allow_methods=["*"],            
    allow_headers=["*"],            
    expose_headers=["*"],           
    max_age=86400,                  
)

# Include routers
app.include_router(websocket.router)
app.include_router(cart.router)
app.include_router(books.router)
app.include_router(auth.router)
app.include_router(member.router)
app.include_router(advertisements.router)
app.include_router(payments.router)
app.include_router(like.router)
app.include_router(ai_search.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to Mini Online Bookstore Backend API", "version": "1.0.0"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}