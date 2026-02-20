"""API router for chat operations."""

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from api.dependencies import get_or_create_chatbot, profile_store
from api.models import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/warmup")
async def warmup(user_id: str, background_tasks: BackgroundTasks):
    """Warmup the chatbot for a user manually."""
    try:
        try:
            profile_store.load(user_id)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="User profile not found. Register first.")

        background_tasks.add_task(get_or_create_chatbot, user_id)
        return {"status": "warming_up", "user_id": user_id}
    except Exception as e:
        logger.error(f"Warmup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with the AI."""
    try:
        user_id = request.user_id
        message = request.message

        try:
            profile_store.load(user_id)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="User profile not found. Register first.")

        # Get chatbot instance
        chatbot = get_or_create_chatbot(user_id)

        # Chat
        response = chatbot.chat(message)

        # chat() returns a plain string; get avatar from chatbot state
        avatar = chatbot.get_current_avatar()
        intent = chatbot.get_last_intent() or "general"

        return ChatResponse(
            response=response,
            agent_avatar=avatar,
            agent_name=intent.replace("_", " ").title(),
        )

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
