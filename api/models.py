"""Pydantic request/response models for the Study Pal API."""

from typing import Optional

from pydantic import BaseModel


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
