"""
FastAPI backend for Study Pal frontend.
Wraps existing Python code to provide REST API endpoints.
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is in path for imports (e.g. core, agents)
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import routers after sys.path setup
from api.routers import chat, documents, users

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validate OPENAI_API_KEY early so errors are clear
if not os.getenv("OPENAI_API_KEY"):
    logger.warning("OPENAI_API_KEY is not set. Chat and RAG features will fail.")

# Initialize FastAPI app
app = FastAPI(title="Study Pal API", version="1.0.0")

# CORS: local dev + optional deployed frontend
_cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
if os.environ.get("ALLOWED_ORIGINS"):
    _cors_origins.extend(o.strip() for o in os.environ["ALLOWED_ORIGINS"].split(",") if o.strip())
if os.environ.get("FRONTEND_URL"):
    _cors_origins.append(os.environ["FRONTEND_URL"].rstrip("/"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(_cors_origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(documents.router, prefix="/api", tags=["documents"])


@app.get("/")
async def root():
    return {"message": "Study Pal API", "status": "running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
