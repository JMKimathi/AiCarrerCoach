from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import seed_database, engine
from backend.app.rag_engine import RAGEngine
from backend.app.routers import auth, chat, resources, feedback, admin, career


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 60)
    print("Starting Strathmore AI Career Coach API Server...")
    if len(settings.SECRET_KEY) < 32:
        raise RuntimeError("Set SECRET_KEY to a random value of at least 32 characters in backend/.env")
    print("1. Initializing and seeding database...")
    seed_database()
    print("2. Initializing optional RAG vector retriever...")
    try:
        RAGEngine.get_instance()
        print("RAG retriever is ready.")
    except Exception as exc:
        # Core API routes (including structured career assessment) can run
        # without the optional trained retriever assets.
        print(f"[RAG] Retriever unavailable; continuing without resource retrieval: {exc}")
    print("System initialization complete. API is ready to accept requests.")
    print("=" * 60)
    yield
    print("Shutting down API server.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API supporting the Strathmore University Intelligent Career Guidance Assistant using RAG.",
    lifespan=lifespan,
)

# Native Android clients do not use CORS. Add trusted browser origins via CORS_ORIGINS if needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(chat.router, prefix=settings.API_PREFIX)
app.include_router(resources.router, prefix=settings.API_PREFIX)
app.include_router(feedback.router, prefix=settings.API_PREFIX)
app.include_router(admin.router, prefix=settings.API_PREFIX)
app.include_router(career.router, prefix=settings.API_PREFIX)


@app.get("/")
def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "docs_url": "/docs",
        "health_check": f"{settings.API_PREFIX}/health",
    }


@app.get(f"{settings.API_PREFIX}/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "retriever_loaded": RAGEngine._instance is not None,
    }
