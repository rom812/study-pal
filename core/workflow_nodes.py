"""
LangGraph Nodes - The Worker Functions.

Each node is a function that:
1. Receives the current state
2. Does some work
3. Returns updates to the state

Think of nodes like workers in a factory assembly line.
Each worker (node) does their job and passes the work to the next worker.
"""

import logging
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI

from core.workflow_state import StudyPalState

logger = logging.getLogger(__name__)


# =============================================================================
# NODE 1: Intent Router - Figures out what the user wants
# =============================================================================

def intent_router_node(state: StudyPalState) -> dict:
    """
    Figure out what the user wants to do.

    This node looks at the user's message and decides:
    - Do they want tutoring help? → Go to tutor
    - Do they want to schedule? → Go to scheduler
    - Do they want to analyze their session? → Go to analyzer

    Args:
        state: The current workflow state (our shared notebook)

    Returns:
        Dictionary with updates to the state (what to write in the notebook)

    Example:
        Input: User says "What is a derivative?"
        Output: Sets next_agent = "tutor" (so graph knows to run tutor next)
    """
    logger.info("🔀 Intent Router: Analyzing user request...")

    # Get the last message from the user
    if not state["messages"]:
        # No messages yet, default to tutor
        logger.info("   No messages yet, defaulting to tutor")
        return {
            "current_intent": "tutor",
            "next_agent": "tutor"
        }

    last_message = state["messages"][-1]

    # Simple keyword-based routing (we'll make this smarter later)
    user_text = last_message.content.lower()

    # Check for keywords to determine intent
    # Look for scheduling patterns (times like "14-15", "2pm-3pm", "from X to Y")
    import re
    time_pattern = re.compile(r'\d{1,2}[-:]\d{1,2}|\d{1,2}\s*(am|pm|to|from)', re.IGNORECASE)
    has_time = bool(time_pattern.search(user_text))

    if any(word in user_text for word in ["schedule", "plan", "calendar", "studying"]) or has_time:
        intent = "schedule"
        next_node = "scheduler"
    elif any(word in user_text for word in ["analyze", "session", "weak points", "finish", "review"]):
        intent = "analyze"
        next_node = "analyzer"
    elif any(word in user_text for word in ["motivate", "encourage", "inspiration"]):
        intent = "motivate"
        next_node = "motivator"
    else:
        # Default to tutoring
        intent = "tutor"
        next_node = "tutor"

    logger.info(f"   ✓ Detected intent: {intent}, routing to {next_node}")

    return {
        "current_intent": intent,
        "next_agent": next_node
    }


# =============================================================================
# NODE 2: Tutor Agent - Answers questions using RAG
# =============================================================================

def tutor_agent_node(state: StudyPalState) -> dict:
    """
    Answer user's questions using the RAG-powered tutor.

    This node:
    1. Gets the user's question from messages
    2. Uses TutorAgent to find relevant context and answer
    3. Adds the answer to messages
    4. Decides where to go next

    Args:
        state: Current workflow state

    Returns:
        Updates with the tutor's response and next routing decision
    """
    logger.info("🎓 Tutor Agent: Processing question...")

    from agents.tutor_agent import TutorAgent
    from core.rag_pipeline import RAGPipeline

    # Create RAG pipeline instance
    # Note: We create a new instance each time because RAGPipeline objects
    # are not serializable and cannot be stored in LangGraph state.
    # The RAGPipeline connects to the same persistent vector store, so data is shared.
    rag_pipeline = RAGPipeline()
    tutor = TutorAgent(rag_pipeline=rag_pipeline)

    # Get the user's question
    last_message = state["messages"][-1]
    question = last_message.content

    logger.info(f"   Question: {question[:50]}...")

    # Get context and generate response
    try:
        context = tutor.get_context(question, k=5)
        logger.info(f"   📚 Retrieved {len(context)} context chunks")
        if context:
            logger.info(f"   First chunk: {context[0][:100]}...")
    except Exception as e:
        # Handle cases where vector store has issues (empty, wrong dimensions, etc.)
        logger.warning(f"   ⚠️  Could not retrieve context: {e}")
        context = []

    # Build a response using the context
    if context:
        # We have context, use it to answer
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

        # Build context string
        context_text = "\n\n".join([f"[Chunk {i+1}]\n{chunk}" for i, chunk in enumerate(context)])

        # Build conversation history for context (last 6 messages = 3 exchanges)
        conversation_history = ""
        recent_messages = state["messages"][-7:-1] if len(state["messages"]) > 1 else []
        if recent_messages:
            conversation_history = "\n\nRecent conversation:\n"
            for msg in recent_messages:
                role = "Student" if isinstance(msg, HumanMessage) else "Tutor"
                conversation_history += f"{role}: {msg.content}\n"

        system_message = """You are a helpful AI tutor assisting a student with their study materials.

Your task:
1. Read the context provided from the student's study materials
2. Read the recent conversation history to understand what the student is asking about
3. Answer their question based on the context and conversation history
4. If the student is answering a quiz question, grade their answer and provide feedback
5. If the context text has formatting issues (like spaces between letters), interpret it as best you can
6. If you can answer from the context, give a clear, helpful answer
7. If the context doesn't help answer the question, say so and summarize what the materials do contain

Be conversational, helpful, and remember what you discussed earlier!"""

        user_message = f"""Context from study materials:
{context_text}
{conversation_history}

Student's current message: {question}

Please respond based on the context and conversation history above."""

        messages = [
            HumanMessage(content=system_message),
            HumanMessage(content=user_message)
        ]

        response = llm.invoke(messages)
        answer = response.content
        logger.info(f"   ✓ Generated answer: {answer[:50]}...")
    else:
        # No context available
        answer = ("I don't have any study materials loaded yet. "
                  "Please upload a PDF using /ingest command first.")
        logger.info("   ⚠️  No study materials available")

    # Update the current topic if we can extract it
    # (For now, we'll keep it simple)

    # Return state updates
    return {
        "messages": [AIMessage(content=answer)],
        "next_agent": "end"  # We're done for now
    }


# =============================================================================
# NODE 3: Scheduler Agent - Creates study schedules
# =============================================================================

def scheduler_agent_node(state: StudyPalState) -> dict:
    """
    Generate a study schedule based on user availability.

    This node uses the SchedulerAgent to create Pomodoro study plans.

    Args:
        state: Current workflow state

    Returns:
        Updates with the generated schedule
    """
    logger.info("📅 Scheduler Agent: Creating study plan...")

    from agents.scheduler_agent import SchedulerAgent
    from core.mcp_connectors import CalendarConnector
    import re

    # Get user's message
    last_message = state["messages"][-1]
    user_input = last_message.content

    logger.info(f"   User availability: {user_input[:50]}...")

    # If user said "schedule my own times" or "from 14-15 tomorrow", extract the time
    # and add a default subject if none provided
    if not any(word in user_input.lower() for word in ["study", "focus", "subject", "topic"]):
        # No subject mentioned, add a default one
        user_input += " studying General Topics"

    # Create scheduler
    calendar_connector = CalendarConnector()
    scheduler = SchedulerAgent(calendar_connector=calendar_connector)

    # Build context
    context = {
        "user_input": user_input,
        "user_id": state["user_id"]
    }

    try:
        # Generate schedule, use weak points if available
        schedule = scheduler.generate_schedule(
            context=context,
            recommendations=state.get("weak_points")
        )

        # Format nice response
        sessions = schedule.get("sessions", [])
        response = f"📚 I've created your study schedule!\n\n"
        response += f"Found {len([s for s in sessions if s['type'] == 'study'])} study sessions:\n\n"

        for idx, session in enumerate(sessions[:5], 1):  # Show first 5
            if session["type"] == "study":
                response += f"{idx}. 📖 {session['start']} - {session['end']}: {session['subject']}\n"

        response += "\nWould you like me to sync this to your calendar?"

        logger.info(f"   ✓ Created schedule with {len(sessions)} sessions")

        return {
            "messages": [AIMessage(content=response)],
            "generated_schedule": schedule,
            "next_agent": "end"
        }

    except Exception as e:
        error_msg = f"Sorry, I had trouble creating a schedule: {str(e)}"
        logger.error(f"   ❌ Error: {e}")

        return {
            "messages": [AIMessage(content=error_msg)],
            "next_agent": "end"
        }


# =============================================================================
# NODE 4: Analyzer Agent - Finds weak points
# =============================================================================

def analyzer_agent_node(state: StudyPalState) -> dict:
    """
    Analyze the conversation to find weak points and make recommendations.

    Args:
        state: Current workflow state with conversation history

    Returns:
        Updates with analysis results
    """
    logger.info("🔍 Analyzer Agent: Analyzing study session...")

    from agents.weakness_detector_agent import WeaknessDetectorAgent

    # Check if we have enough conversation
    if len(state["messages"]) < 4:  # Need at least 2 exchanges
        response = "I need more conversation to analyze. Ask me a few questions first!"
        logger.info("   ⚠️  Not enough conversation to analyze")

        return {
            "messages": [AIMessage(content=response)],
            "next_agent": "end"
        }

    # Analyze with weakness detector
    detector = WeaknessDetectorAgent(model="gpt-4o-mini")

    try:
        result = detector.analyze_conversation(
            state["messages"],
            session_topic=state.get("current_topic")
        )

        # Format the response
        weak_points = result.get("weak_points", [])

        if weak_points:
            response = f"📊 Session Analysis:\n\n"
            response += f"I identified {len(weak_points)} areas to focus on:\n\n"

            for idx, wp in enumerate(weak_points[:3], 1):
                topic = wp.get("topic", "Unknown")
                difficulty = wp.get("difficulty_level", "mild")
                icon = "🔴" if difficulty == "severe" else "🟡" if difficulty == "moderate" else "🟢"

                response += f"{idx}. {icon} {topic.upper()} - {difficulty} difficulty\n"

            response += "\nWould you like me to create a study schedule focusing on these topics?"
        else:
            response = "✅ Great session! No significant difficulties detected."

        logger.info(f"   ✓ Found {len(weak_points)} weak points")

        return {
            "messages": [AIMessage(content=response)],
            "weak_points": result,
            "next_agent": "end"
        }

    except Exception as e:
        error_msg = f"Sorry, I had trouble analyzing the session: {str(e)}"
        logger.error(f"   ❌ Error: {e}")

        return {
            "messages": [AIMessage(content=error_msg)],
            "next_agent": "end"
        }


# =============================================================================
# NODE 5: Motivator Agent - Provides encouragement
# =============================================================================

def motivator_agent_node(state: StudyPalState) -> dict:
    """
    Generate motivational message based on user's persona preference.

    Args:
        state: Current workflow state

    Returns:
        Updates with motivational message
    """
    logger.info("💪 Motivator Agent: Crafting motivation...")

    from agents.motivator_agent import MotivatorAgent, OpenAIMotivationModel
    from agents.quote_store import QuoteStore
    from pathlib import Path

    try:
        # Load quote store
        quote_store = QuoteStore(Path("data/quotes_store.json"))

        # Create motivator
        motivator = MotivatorAgent(
            fetcher=None,
            quote_store=quote_store,
            llm=OpenAIMotivationModel()
        )

        # Generate motivation
        motivation = motivator.craft_message(
            user_id=state["user_id"],
            persona="Steve Jobs"  # Could get from user profile
        )

        response = f"💪 {motivation.text}\n\n— Steve Jobs"
        logger.info("   ✓ Generated motivational message")

        return {
            "messages": [AIMessage(content=response)],
            "next_agent": "end"
        }

    except Exception as e:
        # Fallback if motivation fails
        response = "Keep pushing forward! You're doing great! 🚀"
        logger.warning(f"   ⚠️  Fallback motivation used: {e}")

        return {
            "messages": [AIMessage(content=response)],
            "next_agent": "end"
        }
