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
from typing import Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI

from core.workflow_state import StudyPalState

logger = logging.getLogger(__name__)


def _get_last_human_message(messages: list[BaseMessage]) -> Optional[HumanMessage]:
    """Return the most recent human message from the conversation."""
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return message
    return None


def _contains_any(text: str, keywords: list[str]) -> bool:
    """Utility helper to check if any keyword exists in the given text."""
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


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

    if not state["messages"]:
        logger.info("   No messages yet, defaulting to tutor")
        return {
            "current_intent": "tutor",
            "next_agent": "tutor",
            "needs_motivation": False,
            "start_tutor_after_schedule": False,
            "tutor_exit_requested": False,
        }

    last_user_message = _get_last_human_message(state["messages"])
    if not last_user_message:
        logger.info("   No human message detected, ending turn")
        return {
            "current_intent": "tutor",
            "next_agent": "__end__",
            "needs_motivation": False,
            "start_tutor_after_schedule": False,
            "tutor_exit_requested": False,
        }

    user_text = last_user_message.content.strip()
    normalized = user_text.lower()

    motivation_keywords = ["motivat", "pep talk", "encourag", "inspire", "hype me"]
    analysis_keywords = ["analy", "weak point", "summary", "recap", "reflect"]
    study_keywords = [
        "study",
        "learn",
        "help me",
        "tutor",
        "teach",
        "quiz",
        "practice",
        "explain",
        "walk me through",
        "understand",
        "lesson",
    ]

    awaiting_confirmation = state.get("awaiting_schedule_confirmation", False)
    awaiting_details = state.get("awaiting_schedule_details", False)

    updates = {
        "needs_motivation": False,
        "start_tutor_after_schedule": False,
        "tutor_exit_requested": False,
    }

    if awaiting_details:
        logger.info("   Awaiting schedule details → routing to scheduler")
        updates.update(
            {
                "current_intent": "schedule",
                "next_agent": "scheduler",
                "pending_schedule_request": user_text,
            }
        )
        return updates

    if awaiting_confirmation:
        logger.info("   Awaiting schedule confirmation → routing to scheduler")
        updates.update(
            {
                "current_intent": "schedule",
                "next_agent": "scheduler",
                "pending_schedule_request": user_text,
            }
        )
        return updates

    tutor_active = state.get("tutor_session_active", False)

    is_motivation_intent = _contains_any(normalized, motivation_keywords)
    is_analysis_intent = _contains_any(normalized, analysis_keywords)
    is_study_intent = _contains_any(normalized, study_keywords) or normalized.endswith("?")

    if is_motivation_intent and not tutor_active:
        logger.info("   ✓ Detected motivation intent")
        updates.update(
            {
                "current_intent": "motivate",
                "next_agent": "motivator",
                "needs_motivation": True,
                "session_mode": "motivation_requested",
            }
        )
        return updates

    if is_analysis_intent:
        logger.info("   ✓ Detected analysis intent")
        updates.update(
            {
                "current_intent": "analyze",
                "next_agent": "analyzer",
                "session_mode": "analysis_requested",
                "tutor_session_active": False,
            }
        )
        return updates

    if tutor_active:
        logger.info("   ↺ Active tutoring session detected")
        updates.update(
            {
                "current_intent": "tutor",
                "next_agent": "tutor",
                "session_mode": "active_tutoring",
            }
        )
        return updates

    if is_study_intent:
        logger.info("   ✓ Detected study intent → tutoring track")
        updates.update(
            {
                "current_intent": "tutor",
                "next_agent": "tutor",
                "session_mode": "active_tutoring",
                "tutor_session_active": True,
            }
        )
        return updates

    logger.info("   Defaulting to tutoring track")
    updates.update(
        {
            "current_intent": "tutor",
            "next_agent": "tutor",
            "session_mode": "active_tutoring",
            "tutor_session_active": True,
        }
    )
    return updates


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
    from core.rag_pipeline import get_rag_pipeline

    # Get the user-specific RAG pipeline instance
    # Each user has their own isolated ChromaDB collection to prevent
    # cross-contamination of study materials between users.
    user_id = state.get("user_id", "default_user")
    rag_pipeline = get_rag_pipeline(user_id=user_id)
    tutor = TutorAgent(rag_pipeline=rag_pipeline)

    last_user_message = _get_last_human_message(state["messages"])
    if not last_user_message:
        logger.warning("   ⚠️  No user question available for tutor")
        fallback = "I didn't catch a question to help with. Could you please try asking again?"
        return {
            "messages": [AIMessage(content=fallback)],
            "tutor_session_active": False,
            "session_mode": "active_tutoring",
            "next_agent": "__end__",
            "tutor_exit_requested": False,
        }

    question = last_user_message.content

    logger.info(f"   Question: {question[:50]}...")

    # Get context and generate response
    try:
        context = tutor.get_context(question, k=5)
        logger.info(f"   📚 Retrieved {len(context)} context chunks")
        if context:
            logger.info(f"   First chunk: {context[0][:100]}...")
    except Exception as e:
        logger.warning(f"   ⚠️  Could not retrieve context: {e}")
        context = []

    if context:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

        context_text = "\n\n".join([f"[Chunk {i+1}]\n{chunk}" for i, chunk in enumerate(context)])

        off_topic_keywords = [
            "recipe",
            "cooking",
            "weather",
            "sports",
            "movie",
            "music",
            "game",
            "restaurant",
            "travel",
            "shopping",
            "fashion",
            "celebrity",
            "joke",
        ]

        question_lower = question.lower()
        is_obviously_off_topic = any(keyword in question_lower for keyword in off_topic_keywords)

        if is_obviously_off_topic:
            logger.info("   🔍 Quick relevance check: OFF-TOPIC (keyword match)")
            answer = (
                "I don't have information about that in your study materials. "
                "I'm here to help you learn from your uploaded PDFs. Please ask me about academic topics covered in your materials."
            )

            return {
                "messages": [AIMessage(content=answer)],
                "next_agent": "__end__",
                "tutor_session_active": state.get("tutor_session_active", False),
                "session_mode": state.get("session_mode", "active_tutoring"),
                "tutor_exit_requested": False,
            }

        logger.info("   🔍 Relevance check: PASSED (proceeding to answer)")

        conversation_history = ""
        recent_messages = state["messages"][-7:-1] if len(state["messages"]) > 1 else []
        if recent_messages:
            conversation_history = "\n\nRecent conversation:\n"
            for msg in recent_messages:
                role = "Student" if isinstance(msg, HumanMessage) else "Tutor"
                conversation_history += f"{role}: {msg.content}\n"

        system_message = """You are a strict AI tutor assistant that ONLY teaches from the student's uploaded study materials.

CRITICAL RULES - YOU MUST FOLLOW THESE:
1. ONLY answer questions based on the provided context from study materials
2. If the context does NOT contain information to answer the question, you MUST say:
   "I cannot answer this question based on your study materials. Please ask about topics covered in your uploaded PDFs."
3. NEVER use your general knowledge or make up information
4. NEVER hallucinate or invent facts not in the context
5. If you're unsure, say you don't have enough information in the materials

WHAT YOU CAN DO WHEN CONTEXT IS AVAILABLE:
- Answer questions based STRICTLY on the provided context
- Quote relevant parts from the context when possible
- Create quizzes based on the context
- Grade quiz answers based on the study materials
- Be encouraging and supportive about the material they're learning
- Use the recent conversation history to maintain context and continuity
- If context has formatting issues, interpret it as best you can

Remember: Your job is to help students learn ONLY from their uploaded materials. If the answer is not in the context, you MUST refuse to answer."""

        user_message = f"""Context from study materials:
{context_text}
{conversation_history}

Student's current message: {question}

Please respond based on the context and conversation history above."""

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        response = llm.invoke(messages)
        answer = response.content
        logger.info(f"   ✓ Generated answer: {answer[:50]}...")
    else:
        answer = (
            "I don't have any study materials loaded yet. "
            "Please upload a PDF using /ingest command first."
        )
        logger.info("   ⚠️  No study materials available")

    # Update the current topic if we can extract it
    # (For now, we'll keep it simple)

    # === NEW: Multi-turn tutoring support ===
    # Mark tutoring session as active (enables Tutor → Tutor loops)
    # The route_after_tutor function will decide if we continue or exit
    # based on user intent detection

    # Return state updates
    exit_requested = detect_tutor_exit_intent(state["messages"])
    logger.info(f"   Tutor exit requested: {exit_requested}")

    next_agent = "analyzer" if exit_requested else "__end__"
    session_mode = "analysis_requested" if exit_requested else "active_tutoring"

    return {
        "messages": [AIMessage(content=answer)],
        "tutor_session_active": not exit_requested,
        "session_mode": session_mode,
        "next_agent": next_agent,
        "tutor_exit_requested": exit_requested,
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
    last_message = _get_last_human_message(state["messages"]) or state["messages"][-1]
    user_input = last_message.content

    logger.info(f"   User availability: {user_input[:50]}...")

    awaiting_confirmation = state.get("awaiting_schedule_confirmation", False)
    awaiting_details = state.get("awaiting_schedule_details", False)

    affirmative_words = {"yes", "yeah", "yep", "sure", "affirmative", "please", "ok", "okay", "definitely"}
    negative_words = {"no", "nope", "nah", "cancel", "not now", "later", "stop"}

    normalized = user_input.lower().strip()

    if awaiting_confirmation:
        logger.info("   Handling schedule confirmation response")
        if any(word in normalized.split() for word in affirmative_words) or normalized in affirmative_words:
            message = (
                "Great! When would you like your next study session? "
                "Please share a specific day and time window (e.g., \"Tuesday 14:00-16:00\")."
            )
            return {
                "messages": [AIMessage(content=message)],
                "awaiting_schedule_confirmation": False,
                "awaiting_schedule_details": True,
                "pending_schedule_request": None,
                "user_wants_scheduling": True,
                "session_mode": "scheduling_requested",
                "next_agent": "__end__",
            }

        if any(word in normalized for word in negative_words):
            message = "No problem! If you change your mind, just let me know and we can plan the next session together."
            return {
                "messages": [AIMessage(content=message)],
                "awaiting_schedule_confirmation": False,
                "awaiting_schedule_details": False,
                "pending_schedule_request": None,
                "user_wants_scheduling": False,
                "session_mode": "analysis_completed",
                "next_agent": "__end__",
            }

        message = "Just let me know with a simple \"yes\" or \"no\" if you'd like me to schedule your next session."
        return {
            "messages": [AIMessage(content=message)],
            "awaiting_schedule_confirmation": True,
            "awaiting_schedule_details": False,
            "pending_schedule_request": None,
            "user_wants_scheduling": False,
            "next_agent": "__end__",
        }

    if awaiting_details:
        logger.info("   Collecting schedule details from user")

        if any(word in normalized for word in negative_words):
            message = "All right! We can plan another time whenever you're ready."
            return {
                "messages": [AIMessage(content=message)],
                "awaiting_schedule_confirmation": False,
                "awaiting_schedule_details": False,
                "pending_schedule_request": None,
                "user_wants_scheduling": False,
                "session_mode": "analysis_completed",
                "next_agent": "__end__",
            }

        day_keywords = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
            "today",
            "tomorrow",
            "tonight",
            "weekend",
        ]
        has_day_reference = any(day in normalized for day in day_keywords)
        time_pattern = re.compile(r"\b\d{1,2}(:\d{2})?\s*(am|pm)?\b|\b\d{1,2}\s*[-:to]{1,3}\s*\d{1,2}", re.IGNORECASE)
        has_time_reference = bool(time_pattern.search(normalized))

        if not (has_day_reference and has_time_reference):
            message = (
                "To lock in the session, I need both a day and a time window. "
                "For example: \"Thursday from 18:00-20:00\" or \"Saturday 10am-12pm\"."
            )
            return {
                "messages": [AIMessage(content=message)],
                "awaiting_schedule_confirmation": False,
                "awaiting_schedule_details": True,
                "pending_schedule_request": None,
                "user_wants_scheduling": True,
                "next_agent": "__end__",
            }
        # Continue to scheduling flow with the provided details

    # Check if user is responding "yes" to sync an existing schedule
    if state.get("generated_schedule") is not None:
        # Check if user wants to sync
        affirmative_words = ["yes", "yeah", "sure", "ok", "okay", "y", "yep", "please", "sync"]
        if any(word in user_input.lower() for word in affirmative_words):
            logger.info("   User confirmed calendar sync")

            # Sync to calendar
            calendar_connector = CalendarConnector()
            scheduler = SchedulerAgent(calendar_connector=calendar_connector)

            try:
                scheduler.sync_schedule(state["generated_schedule"])
                response = "✅ Great! I've synced your study schedule to your calendar. You should see the events appear shortly!"
                logger.info("   ✓ Successfully synced schedule to calendar")

                return {
                    "messages": [AIMessage(content=response)],
                    "next_agent": "__end__",
                    "start_tutor_after_schedule": False,
                    "ready_for_tutoring": False,
                    "session_mode": "scheduled",
                    "user_wants_scheduling": False,
                    "awaiting_schedule_confirmation": False,
                    "awaiting_schedule_details": False,
                    "pending_schedule_request": state.get("pending_schedule_request"),
                }
            except Exception as e:
                response = f"⚠️ I had trouble syncing to your calendar: {str(e)}\n\nYour schedule is still saved, but it wasn't added to your calendar."
                logger.error(f"   ❌ Calendar sync error: {e}")

                return {
                    "messages": [AIMessage(content=response)],
                    "next_agent": "__end__",
                    "start_tutor_after_schedule": False,
                    "ready_for_tutoring": False,
                    "user_wants_scheduling": False,
                    "awaiting_schedule_confirmation": False,
                    "awaiting_schedule_details": False,
                    "pending_schedule_request": state.get("pending_schedule_request"),
                }

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
        # === NEW: Use analysis results from Analyzer → Scheduler handoff ===
        # If analysis_results exist in state, use them for prioritization
        analysis_results = state.get("session_analysis") or state.get("analysis_results")
        stored_weak_points = state.get("weak_points")

        prioritized_recommendations = stored_weak_points
        if not prioritized_recommendations and analysis_results:
            if hasattr(analysis_results, "weak_points"):
                prioritized_recommendations = analysis_results.weak_points
            elif isinstance(analysis_results, dict) and "weak_points" in analysis_results:
                prioritized_recommendations = analysis_results["weak_points"]

        # Generate schedule, use weak points if available
        schedule = scheduler.generate_schedule(
            context=context,
            recommendations=prioritized_recommendations
        )

        # Format nice response
        sessions = schedule.get("sessions", [])
        response = f"📚 I've created your study schedule!\n\n"

        # === NEW: Reference analysis in scheduling response ===
        if analysis_results and hasattr(analysis_results, 'weak_points') and analysis_results.weak_points:
            weak_topics = [wp.topic for wp in analysis_results.weak_points[:3]]
            response += f"📊 Based on your session analysis, I've prioritized: {', '.join(weak_topics)}\n\n"

        response += f"Found {len([s for s in sessions if s['type'] == 'study'])} study sessions:\n\n"

        for idx, session in enumerate(sessions[:5], 1):  # Show first 5
            if session["type"] == "study":
                response += f"{idx}. 📖 {session['start']} - {session['end']}: {session['subject']}\n"

        response += "\nWould you like me to sync this to your calendar?"

        logger.info(f"   ✓ Created schedule with {len(sessions)} sessions")
        should_start_tutor = state.get("start_tutor_after_schedule", False)

        return {
            "messages": [AIMessage(content=response)],
            "generated_schedule": schedule,
            "schedule_plan": schedule,
            "session_mode": "active_tutoring" if should_start_tutor else "scheduled",
            "tutor_session_active": should_start_tutor,
            "ready_for_tutoring": should_start_tutor,
            "start_tutor_after_schedule": False,
            "user_wants_scheduling": False,
            "awaiting_schedule_confirmation": False,
            "awaiting_schedule_details": False,
            "pending_schedule_request": user_input,
            "next_agent": "tutor" if should_start_tutor else "__end__",
        }

    except Exception as e:
        error_msg = f"Sorry, I had trouble creating a schedule: {str(e)}"
        logger.error(f"   ❌ Error: {e}")

        return {
            "messages": [AIMessage(content=error_msg)],
            "next_agent": "__end__",
            "ready_for_tutoring": False,
            "start_tutor_after_schedule": False,
            "user_wants_scheduling": False,
            "awaiting_schedule_confirmation": False,
            "awaiting_schedule_details": True if awaiting_details else False,
            "pending_schedule_request": None if awaiting_details else state.get("pending_schedule_request"),
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
            "next_agent": "__end__",
            "tutor_session_active": False,
            "session_mode": "analysis_completed",
            "needs_motivation": False,
            "user_wants_scheduling": False,
            "awaiting_schedule_confirmation": False,
            "awaiting_schedule_details": False,
        }

    # Analyze with weakness detector
    detector = WeaknessDetectorAgent(model="gpt-4o-mini")

    try:
        result = detector.analyze_conversation(
            state["messages"],
            session_topic=state.get("current_topic")
        )

        # result is a SessionRecommendations dataclass object
        weak_points = getattr(result, "weak_points", None)

        bullet_lines = []
        if weak_points:
            bullet_lines.append(f"I identified {len(weak_points)} areas to focus on:\n")
            for idx, wp in enumerate(weak_points[:3], 1):
                topic = getattr(wp, "topic", "Concept")
                difficulty = getattr(wp, "difficulty_level", "moderate")
                icon = "🔴" if difficulty == "severe" else "🟡" if difficulty == "moderate" else "🟢"
                bullet_lines.append(f"{idx}. {icon} {topic.upper()} — {difficulty} difficulty")
        else:
            bullet_lines.append("I didn't spot any major trouble areas this time — nice work!")

        response = "📊 Session Analysis:\n\n" + "\n".join(bullet_lines)
        response += "\n\nWould you like me to schedule another study session for you? (yes/no)"

        logger.info(f"   ✓ Analysis complete; awaiting scheduling confirmation")

        return {
            "messages": [AIMessage(content=response)],
            "weak_points": weak_points,
            "analysis_results": result,
            "session_analysis": result,
            "user_wants_scheduling": False,
            "needs_motivation": False,
            "session_mode": "analysis_completed",
            "tutor_session_active": False,
            "awaiting_schedule_confirmation": True,
            "awaiting_schedule_details": False,
            "pending_schedule_request": None,
            "next_agent": "__end__",
        }

    except Exception as e:
        error_msg = f"Sorry, I had trouble analyzing the session: {str(e)}"
        logger.error(f"   ❌ Error: {e}")

        return {
            "messages": [AIMessage(content=error_msg)],
            "next_agent": "__end__",
            "needs_motivation": False,
            "awaiting_schedule_confirmation": False,
            "awaiting_schedule_details": False,
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
    from agents.user_profile import UserProfileStore, UserProfile
    from pathlib import Path

    try:
        # Load user profile store
        profile_store = UserProfileStore(Path("data/profiles"))

        # Hydrate profile preferences from workflow state if provided
        user_profile_data = state.get("user_profile") or {}
        profile = None
        if profile_store:
            try:
                profile = profile_store.load(state["user_id"])
            except FileNotFoundError:
                profile = UserProfile(user_id=state["user_id"], name=state["user_id"])

            if profile:
                preferred_persona = user_profile_data.get("favorite_persona")
                preferred_name = user_profile_data.get("name")

                if preferred_persona:
                    profile.primary_persona = preferred_persona
                if preferred_name:
                    profile.name = preferred_name

                profile_store.save(profile)

        # Create motivator
        motivator = MotivatorAgent(
            profile_store=profile_store,
            llm=OpenAIMotivationModel()
        )

        # Generate motivation
        motivation = motivator.craft_personalized_message(
            user_id=state["user_id"]
        )

        response = f"{motivation.text}"
        logger.info("   ✓ Generated motivational message")

        return {
            "messages": [AIMessage(content=response)],
            "next_agent": "__end__",
            "needs_motivation": False,
            "session_mode": "complete",
            "tutor_session_active": False,
        }

    except Exception as e:
        # Fallback if motivation fails
        response = "Keep pushing forward! You're doing great! 🚀"
        logger.warning(f"   ⚠️  Fallback motivation used: {e}")

        return {
            "messages": [AIMessage(content=response)],
            "next_agent": "__end__",
            "needs_motivation": False,
            "session_mode": "complete",
            "tutor_session_active": False,
        }


# =============================================================================
# NEW: Conditional Routing Functions for Multi-Agent Orchestration
# =============================================================================

def detect_tutor_exit_intent(messages: list) -> bool:
    """
    Use LLM to detect if the user wants to end the tutoring session.

    This function analyzes the conversation to determine if the user is signaling
    they want to finish tutoring and move to analysis/scheduling.

    Exit signals include:
    - "I'm done", "that's all", "finish", "end session"
    - "I understand now", "got it, thanks"
    - "Can you analyze my session?"
    - Implicit completion: "thank you, bye"

    Args:
        messages: List of conversation messages

    Returns:
        bool: True if user wants to exit tutoring, False if they want to continue

    Example:
        >>> detect_tutor_exit_intent([
        ...     HumanMessage("What is calculus?"),
        ...     AIMessage("Calculus is..."),
        ...     HumanMessage("Thanks, I'm done for now")
        ... ])
        True
    """
    if len(messages) < 2:
        # Need at least 1 exchange to detect exit intent
        return False

    # Get last 4 messages (2 exchanges) for context
    recent_messages = messages[-4:]
    last_user_message = None

    # Find the last user message
    for msg in reversed(recent_messages):
        if isinstance(msg, HumanMessage):
            last_user_message = msg.content
            break

    if not last_user_message:
        return False

    # Quick keyword check for obvious exit signals (avoid LLM call if possible)
    exit_keywords = [
        "done", "finish", "end", "stop", "enough", "that's all",
        "analyze", "session summary", "weak points", "schedule",
        "bye", "goodbye", "see you", "thanks for your help"
    ]

    user_text_lower = last_user_message.lower()
    has_exit_keyword = any(keyword in user_text_lower for keyword in exit_keywords)

    if has_exit_keyword:
        # Use LLM for nuanced detection to avoid false positives
        # (e.g., "I'm done with this problem" vs "I'm done for today")
        try:
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

            detection_prompt = f"""You are analyzing a tutoring conversation to detect if the user wants to END the tutoring session.

Recent conversation:
{chr(10).join([f"{msg.__class__.__name__}: {msg.content}" for msg in recent_messages])}

Analyze the LAST user message: "{last_user_message}"

Does the user want to:
A) END the tutoring session and move on (analyze their session, schedule, or just finish)
B) CONTINUE with more questions or the current topic

Reply with ONLY one word: "END" or "CONTINUE"

Examples of END signals:
- "I'm done for today, can you analyze my weak points?"
- "Thanks, that's all I needed"
- "Okay I understand now, let's finish up"
- "Great! Can you create a schedule for me?"

Examples of CONTINUE signals:
- "I'm done with this problem, can you give me another one?"
- "That's all for calculus, can you help me with physics?"
- "Okay, what about derivatives?"
"""

            response = llm.invoke([SystemMessage(content=detection_prompt)])
            decision = response.content.strip().upper()

            logger.info(f"🔍 Exit intent detection: '{last_user_message}' → {decision}")

            return decision == "END"

        except Exception as e:
            logger.warning(f"⚠️  Exit intent detection failed, defaulting to CONTINUE: {e}")
            # Default to continue on error (safer to keep user in tutoring)
            return False

    # No exit keywords detected
    return False


def route_after_tutor(state: StudyPalState) -> str:
    """
    Conditional routing after tutor agent completes.

    Decides where to go next after a tutoring interaction:
    - To "analyzer" if user wants to end session (Tutor → Analyzer)
    - To END otherwise (wait for next user message)

    NOTE: We DON'T loop back to tutor here! The tutor loop happens naturally:
    1. User asks question → Intent Router → Tutor → END
    2. User asks another question → Intent Router → Tutor → END
    3. User says "I'm done" → Intent Router detects "finish" → Analyzer

    Args:
        state: Current workflow state

    Returns:
        str: Next node name ("analyzer" or "__end__")

    Flow Logic:
        1. Check if workflow_complete flag is set → END
        2. Detect exit intent from messages → "analyzer"
        3. Otherwise → END (wait for next user message)
    """
    logger.info("🔀 Routing after Tutor...")

    if state.get("workflow_complete", False):
        logger.info("   → END (workflow_complete=True)")
        return "__end__"

    next_node = state.get("next_agent", "__end__")
    if next_node == "analyzer":
        logger.info("   → ANALYZER (tutor exit requested)")
        return "analyzer"

    logger.info("   → END (continuing tutoring loop on next user turn)")
    return "__end__"


def route_after_analyzer(state: StudyPalState) -> str:
    """
    Conditional routing after analyzer agent completes.

    Analyzer now presents the summary and pauses for the user's response.
    The next turn is driven by the intent router, so we simply end here.

    Args:
        state: Current workflow state

    Returns:
        str: Next node name ("scheduler" or "__end__")

    Flow Logic:
        → END (wait for user reply that the router will handle)
    """
    logger.info("🔀 Routing after Analyzer → END (awaiting user response)")
    return "__end__"


def route_after_scheduler(state: StudyPalState) -> str:
    """
    Conditional routing after scheduler agent completes.

    Determines if the workflow should transition directly into tutoring (for
    immediate study sessions), deliver motivation, or pause until the user
    provides the next instruction.
    """
    logger.info("🔀 Routing after Scheduler...")

    next_node = state.get("next_agent", "__end__")

    if next_node == "tutor":
        logger.info("   → TUTOR (schedule confirmed, starting tutoring session)")
        return "tutor"

    if next_node == "motivator":
        logger.info("   → MOTIVATOR (motivation requested post-schedule)")
        return "motivator"

    logger.info("   → END (awaiting next user input)")
    return "__end__"
