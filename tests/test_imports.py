"""Test imports step by step to find where it hangs."""

print("1. Testing basic imports...")
import os
import logging
from pathlib import Path
print("✓ Basic imports OK")

print("2. Testing dotenv...")
from dotenv import load_dotenv
load_dotenv()
print("✓ dotenv OK")

print("3. Testing langchain core...")
from langchain_core.messages import HumanMessage, AIMessage
print("✓ langchain_core OK")

print("4. Testing OpenAI...")
from langchain_openai import ChatOpenAI
print("✓ OpenAI OK")

print("5. Testing user profile...")
from agents.user_profile import UserProfileStore, UserProfile
print("✓ user_profile OK")

print("6. Testing workflow_state...")
from core.workflow_state import StudyPalState
print("✓ workflow_state OK")

print("7. Testing agent_avatars...")
from core.agent_avatars import get_agent_avatar
print("✓ agent_avatars OK")

print("8. Testing vector_stores...")
from core.vector_stores import ChromaVectorStore
print("✓ vector_stores OK")

print("9. Testing rag_pipeline...")
from core.rag_pipeline import get_rag_pipeline
print("✓ rag_pipeline OK")

print("10. Testing workflow_nodes...")
from core.workflow_nodes import intent_router_node
print("✓ workflow_nodes OK")

print("11. Testing workflow_graph...")
from core.workflow_graph import create_study_pal_graph
print("✓ workflow_graph OK")

print("12. Testing langgraph_chatbot...")
from core.langgraph_chatbot import LangGraphChatbot
print("✓ langgraph_chatbot OK")

print("\n✅ ALL IMPORTS SUCCESSFUL!")
