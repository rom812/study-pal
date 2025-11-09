"""
LangGraph-powered chatbot interface.

This replaces the simple TutorChatbot with a multi-agent LangGraph workflow.
Now all agents (Tutor, Scheduler, Analyzer, Motivator) work together automatically!
"""

import logging
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage

from core.workflow_graph import create_study_pal_graph
from agents.tutor_agent import TutorAgent
from core.rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)


class LangGraphChatbot:
    """
    Multi-agent chatbot powered by LangGraph.

    This automatically routes user messages to the right agent:
    - Questions about study materials → Tutor Agent
    - Scheduling requests → Scheduler Agent
    - Session analysis → Analyzer Agent
    - Motivation requests → Motivator Agent

    Example:
        chatbot = LangGraphChatbot(user_id="alice")
        response = chatbot.chat("What is calculus?")
        # Automatically goes to Tutor Agent!

        response = chatbot.chat("Schedule study time from 2-5pm")
        # Automatically goes to Scheduler Agent!
    """

    def __init__(self, user_id: str = "default_user", session_id: str = "default"):
        """
        Initialize the LangGraph chatbot.

        Args:
            user_id: User identifier
            session_id: Conversation session ID (for memory across turns)
        """
        self.user_id = user_id
        self.session_id = session_id

        # Create the LangGraph workflow
        logger.info(f"[LangGraph Chatbot] Initializing for user: {user_id}")
        self.graph = create_study_pal_graph()

        # Initialize RAG pipeline and tutor agent for direct material management
        self.rag_pipeline = RAGPipeline()
        self.tutor_agent = TutorAgent(rag_pipeline=self.rag_pipeline)

        # Keep track of conversation state
        # NOTE: Do NOT add non-serializable objects (like rag_pipeline) here!
        # LangGraph uses msgpack serialization for state persistence.
        self.conversation_state = {
            "messages": [],
            "user_id": user_id,
            "current_topic": None,
            "current_intent": None,
            "weak_points": None,
            "generated_schedule": None,
            "next_agent": None,
            "workflow_complete": False,
        }

        # Add memory interface that ChatInterface expects
        # This is a simple wrapper around conversation_state["messages"]
        from langchain_community.chat_message_histories import ChatMessageHistory
        self.memory = ChatMessageHistory()

        # For session analysis
        self.last_recommendations = None

        logger.info("[LangGraph Chatbot] Ready! All agents standing by.")

    def chat(self, user_message: str) -> str:
        """
        Send a message and get a response from the appropriate agent.

        The workflow automatically:
        1. Figures out what you want (intent routing)
        2. Calls the right agent
        3. Returns their response

        Args:
            user_message: What the user said

        Returns:
            Response from the appropriate agent

        Example:
            >>> chatbot.chat("What is a derivative?")
            "A derivative measures the rate of change..."  # From Tutor

            >>> chatbot.chat("Schedule my study time 2-5pm")
            "I've created your study schedule..."  # From Scheduler
        """
        logger.info(f"[User → LangGraph] {user_message[:50]}...")

        # Add user message to state
        self.conversation_state["messages"].append(HumanMessage(content=user_message))

        # Also add to memory for ChatInterface compatibility
        self.memory.add_user_message(user_message)

        # Configuration for memory (so it remembers across turns)
        config = {"configurable": {"thread_id": self.session_id}}

        try:
            # Run the workflow!
            result_state = self.graph.invoke(self.conversation_state, config)

            # Update our internal state
            self.conversation_state = result_state

            # Sync all messages to memory
            self.memory.clear()
            for msg in result_state["messages"]:
                if isinstance(msg, HumanMessage):
                    self.memory.add_user_message(msg.content)
                elif isinstance(msg, AIMessage):
                    self.memory.add_ai_message(msg.content)

            # Get the last AI message (the response)
            for msg in reversed(result_state["messages"]):
                if isinstance(msg, AIMessage):
                    response = msg.content
                    logger.info(f"[LangGraph → User] {response[:50]}...")
                    return response

            return "I'm not sure how to respond to that."

        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            logger.error(f"[LangGraph Error] {e}")
            return error_msg

    def ingest_material(self, pdf_path: Path) -> str:
        """
        Load study materials into the knowledge base.

        This directly uses the TutorAgent to ingest PDFs.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Status message

        Example:
            >>> chatbot.ingest_material(Path("calculus.pdf"))
            "Successfully ingested calculus.pdf (42 chunks)"
        """
        try:
            num_chunks = self.tutor_agent.ingest_material(pdf_path)
            return f"Successfully ingested {pdf_path.name} ({num_chunks} chunks)"
        except Exception as e:
            return f"Error ingesting {pdf_path.name}: {e}"

    def get_materials_count(self) -> int:
        """Get number of document chunks in knowledge base."""
        return self.tutor_agent.count_materials()

    def clear_materials(self) -> str:
        """Clear all study materials."""
        self.tutor_agent.clear_materials()
        return "All study materials cleared."

    def clear_conversation(self) -> str:
        """Clear conversation history."""
        self.conversation_state = {
            "messages": [],
            "user_id": self.user_id,
            "current_topic": None,
            "current_intent": None,
            "weak_points": None,
            "generated_schedule": None,
            "next_agent": None,
            "workflow_complete": False,
        }
        return "Conversation history cleared."

    def get_conversation_summary(self) -> str:
        """Get summary of current conversation."""
        num_messages = len(self.conversation_state["messages"])
        if num_messages > 0:
            num_exchanges = num_messages // 2
            return f"Conversation: {num_messages} messages ({num_exchanges} exchanges)"
        return "Conversation: No messages yet"

    def get_last_intent(self) -> str:
        """Get the intent detected in the last message."""
        return self.conversation_state.get("current_intent", "unknown")

    def get_weak_points(self) -> dict:
        """Get analysis of weak points from last analysis."""
        return self.conversation_state.get("weak_points")

    def get_schedule(self) -> dict:
        """Get the last generated schedule."""
        return self.conversation_state.get("generated_schedule")

    def analyze_session(self, session_topic: str = None):
        """
        Analyze the current tutoring session to identify weak points.

        Args:
            session_topic: Optional topic that was studied

        Returns:
            SessionRecommendations with weak points and study suggestions
        """
        from agents.weakness_detector_agent import WeaknessDetectorAgent
        from core.weakness_analyzer import SessionRecommendations, WeakPoint, RecommendationBuilder

        # Use the weakness detector agent for LLM-based analysis
        detector = WeaknessDetectorAgent(model="gpt-4o-mini")
        result = detector.analyze_conversation(
            self.conversation_state["messages"],
            session_topic=session_topic
        )

        # Convert LLM result to WeakPoint objects
        weak_points = []
        for wp_data in result.get("weak_points", []):
            weak_point = WeakPoint(
                topic=wp_data.get("topic", "unknown"),
                difficulty_level=wp_data.get("difficulty_level", "mild"),
                evidence=wp_data.get("evidence", []),
                frequency=1,
                confusion_indicators=len(wp_data.get("evidence", [])),
            )
            weak_points.append(weak_point)

        # Build recommendations from weak points
        priority_topics = [wp.topic for wp in weak_points[:5]]
        suggested_focus_time = RecommendationBuilder.calculate_focus_time(weak_points)
        study_tips = RecommendationBuilder.generate_study_tips(weak_points)
        summary = result.get("session_summary", "Session analyzed")

        recommendations = SessionRecommendations(
            weak_points=weak_points,
            priority_topics=priority_topics,
            suggested_focus_time=suggested_focus_time,
            study_approach_tips=study_tips,
            session_summary=summary,
        )

        # Save recommendations for scheduler integration
        self.last_recommendations = recommendations

        # Also update conversation state
        self.conversation_state["weak_points"] = result

        return recommendations
