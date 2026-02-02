"""
FastAPI backend for Study Pal frontend.
Wraps existing Python code to provide REST API endpoints.
"""

import os
import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import existing Study Pal modules
# Note: These imports assume the API is run from project root with PYTHONPATH set
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import user_profile directly to avoid agents/__init__.py (which pulls in chromadb/jsonschema)
# Bypass avoids: chromadb -> jsonschema_specifications JSONDecodeError on some systems
import types
_agents = types.ModuleType("agents")
_agents.__path__ = [str(project_root / "agents")]
sys.modules["agents"] = _agents
from agents.user_profile import UserProfile, UserProfileStore

# Lazy import LangGraphChatbot - only import when needed
LangGraphChatbot = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Study Pal API", version="1.0.0")

# CORS: local dev + optional deployed frontend (e.g. Vercel)
_cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
if os.environ.get("ALLOWED_ORIGINS"):
    _cors_origins.extend(o.strip() for o in os.environ["ALLOWED_ORIGINS"].split(",") if o.strip())
if os.environ.get("FRONTEND_URL"):
    _cors_origins.append(os.environ["FRONTEND_URL"].rstrip("/"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(_cors_origins)),  # dedupe
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize profile store (relative to project root)
PROFILES_DIR = project_root / "data" / "profiles"
PROFILES_DIR.mkdir(parents=True, exist_ok=True)
profile_store = UserProfileStore(PROFILES_DIR)

# Store chatbot instances per user
chatbot_instances: dict = {}


def get_or_create_chatbot(user_id: str):
    """Get or create a chatbot instance for a user."""
    global LangGraphChatbot
    # Lazy import to avoid blocking on startup
    if LangGraphChatbot is None:
        logger.info("Lazy loading LangGraphChatbot...")
        from core.langgraph_chatbot import LangGraphChatbot as _LangGraphChatbot
        LangGraphChatbot = _LangGraphChatbot
    
    if user_id not in chatbot_instances:
        logger.info(f"Creating chatbot instance for user: {user_id}")
        chatbot_instances[user_id] = LangGraphChatbot(user_id=user_id, session_id=user_id)
        logger.info(f"Chatbot instance created for user: {user_id}")
    return chatbot_instances[user_id]


# Pydantic models for request/response
class RegisterRequest(BaseModel):
    user_id: str
    name: str
    primary_persona: str
    preferred_personas: list[str]
    academic_field: Optional[str] = None
    study_topics: list[str] = []
    goals: list[str] = []
    traits: list[str] = []


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    agent_avatar: str
    agent_name: str


class ProfileResponse(BaseModel):
    user_id: str
    name: str
    primary_persona: str
    preferred_personas: list[str]
    academic_field: Optional[str] = None
    study_topics: list[str] = []
    goals: list[str] = []
    traits: list[str] = []


# API Routes
@app.get("/")
async def root():
    return {"message": "Study Pal API", "status": "running"}


@app.get("/api/profile/{user_id}", response_model=ProfileResponse)
async def get_profile(user_id: str):
    """Get user profile by user_id."""
    try:
        profile = profile_store.load(user_id)
        return ProfileResponse(
            user_id=profile.user_id,
            name=profile.name,
            primary_persona=profile.primary_persona,
            preferred_personas=profile.preferred_personas,
            academic_field=profile.academic_field,
            study_topics=profile.study_topics,
            goals=profile.goals,
            traits=profile.traits,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="User profile not found")
    except Exception as e:
        logger.error(f"Error loading profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/register", response_model=ProfileResponse)
async def register(request: RegisterRequest):
    """Create a new user profile."""
    try:
        # Check if user already exists
        try:
            existing = profile_store.load(request.user_id)
            raise HTTPException(status_code=400, detail="User ID already exists")
        except FileNotFoundError:
            pass  # User doesn't exist, proceed with registration

        # Create profile
        profile = UserProfile(
            user_id=request.user_id,
            name=request.name,
            primary_persona=request.primary_persona,
            preferred_personas=request.preferred_personas,
            academic_field=request.academic_field,
            study_topics=request.study_topics,
            goals=request.goals,
            traits=request.traits,
            current_focus=request.study_topics[0] if request.study_topics else None,
        )

        # Save profile
        profile_store.save(profile)
        logger.info(f"Created profile for user: {request.user_id}")

        return ProfileResponse(
            user_id=profile.user_id,
            name=profile.name,
            primary_persona=profile.primary_persona,
            preferred_personas=profile.preferred_personas,
            academic_field=profile.academic_field,
            study_topics=profile.study_topics,
            goals=profile.goals,
            traits=profile.traits,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a chat message and get response."""
    try:
        # Get or create chatbot instance
        chatbot = get_or_create_chatbot(request.user_id)

        # Send message
        response_text = chatbot.chat(request.message)

        # Get current agent avatar
        agent_avatar = chatbot.get_current_avatar()
        current_intent = chatbot.get_last_intent()

        # Map intent to agent name
        agent_name_map = {
            "tutor": "Tutor",
            "scheduler": "Scheduler",
            "analyzer": "Analyzer",
            "motivator": "Motivator",
            "unknown": "System",
        }
        agent_name = agent_name_map.get(current_intent, "System")

        return ChatResponse(
            response=response_text,
            agent_avatar=agent_avatar,
            agent_name=agent_name,
        )
    except Exception as e:
        logger.error(f"Error in chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload")
async def upload_file(
    user_id: str = Form(...),
    file: UploadFile = File(...),
):
    """Upload a PDF file for ingestion."""
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        # Get or create chatbot instance
        chatbot = get_or_create_chatbot(user_id)

        # Save uploaded file temporarily
        upload_dir = project_root / "data" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_path = upload_dir / file.filename

        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        try:
            # Ingest the file
            result = chatbot.ingest_material(temp_path)
            chunks = chatbot.get_materials_count()

            return {
                "message": result,
                "chunks": chunks,
            }
        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

