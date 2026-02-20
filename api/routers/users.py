"""API router for user operations."""

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from api.dependencies import UserProfile, get_or_create_chatbot, profile_store
from api.models import ProfileResponse, RegisterRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/profile/{user_id}", response_model=ProfileResponse)
async def get_profile(user_id: str):
    """Get a user profile by ID."""
    try:
        profile = profile_store.load(user_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    return profile


@router.post("/auth/register")
async def register(request: RegisterRequest, background_tasks: BackgroundTasks):
    """Register a new user."""
    user_id = request.user_id
    try:
        profile_store.load(user_id)
        raise HTTPException(status_code=400, detail="User already exists")
    except FileNotFoundError:
        pass  # Expected — user doesn't exist yet

    # Create profile
    profile = UserProfile(
        user_id=user_id,
        name=request.name,
        primary_persona=request.primary_persona,
        preferred_personas=request.preferred_personas,
        academic_field=request.academic_field,
        study_topics=request.study_topics,
        goals=request.goals,
        traits=request.traits,
    )
    profile_store.save(profile)

    # Warmup chatbot in background
    background_tasks.add_task(get_or_create_chatbot, user_id)

    return profile
