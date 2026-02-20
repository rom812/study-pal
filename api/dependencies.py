"""Shared dependencies for API routes."""

import importlib.util
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Import user_profile directly to avoid agents/__init__.py pulling in chromadb/jsonschema
_user_profile_path = PROJECT_ROOT / "agents" / "user_profile.py"
_spec = importlib.util.spec_from_file_location("user_profile", _user_profile_path)
_user_profile = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_user_profile)
UserProfile = _user_profile.UserProfile
UserProfileStore = _user_profile.UserProfileStore
UserProgressEvent = _user_profile.UserProgressEvent

UserProfile.model_rebuild(
    _types_namespace={
        "datetime": datetime,
        "Literal": Literal,
        "UserProgressEvent": UserProgressEvent,
    }
)

# Profile store
PROFILES_DIR = PROJECT_ROOT / "data" / "profiles"
PROFILES_DIR.mkdir(parents=True, exist_ok=True)
profile_store = UserProfileStore(PROFILES_DIR)

# Chatbot instances (lazy-loaded)
LangGraphChatbot = None
chatbot_instances: dict = {}
_chatbot_lock = threading.Lock()


def get_or_create_chatbot(user_id: str):
    """Get or create a chatbot instance for a user."""
    global LangGraphChatbot
    with _chatbot_lock:
        if LangGraphChatbot is None:
            logger.info("Lazy loading LangGraphChatbot...")
            from core.langgraph_chatbot import LangGraphChatbot as _LangGraphChatbot

            LangGraphChatbot = _LangGraphChatbot

        if user_id not in chatbot_instances:
            logger.info(f"Creating chatbot instance for user: {user_id}")
            chatbot_instances[user_id] = LangGraphChatbot(user_id=user_id, session_id=user_id)
        return chatbot_instances[user_id]
