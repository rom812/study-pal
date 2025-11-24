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
from core.agent_avatars import get_agent_avatar

logger = logging.getLogger(__name__)


def _get_last_human_message(messages: list[BaseMessage]) -> Optional[HumanMessage]:
    """Return the most recent human message from the conversation."""
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return message
    return None


def _format_history(messages: list[BaseMessage], last_n: int = 3) -> str:
    """
    Format last N messages for LLM context.

    Args:
        messages: List of conversation messages
        last_n: Number of recent messages to include

    Returns:
        Formatted string with recent conversation history
    """
    if not messages:
        return "No previous conversation."

    recent = messages[-last_n:] if len(messages) > last_n else messages
    formatted = []
    for msg in recent:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        content = msg.content[:150] + "..." if len(msg.content) > 150 else msg.content
        formatted.append(f"{role}: {content}")
    return "\n".join(formatted)


# =============================================================================
# LLM-Based Intent Classification
# =============================================================================

def classify_intent_with_llm(user_message: str, conversation_history: list[BaseMessage]) -> str:
    """
    Use LLM to classify user intent with full conversation context.

    Returns: tutor, scheduler, analyzer, or motivator
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Format conversation history for context
    history_text = _format_history(conversation_history, last_n=4)

    prompt = f"""You are an intelligent intent classifier for a study assistant.

Analyze the user's message AND the conversation history to determine their intent.

CATEGORIES:
- tutor: User wants to learn, ask questions, create/take quizzes, get explanations, study topics
- scheduler: User wants to SCHEDULE study time, plan sessions, set up calendar events
- analyzer: User wants to ANALYZE their study session, review progress, get weak points analysis, or indicates they're done/finished with tutoring
- motivator: User wants motivation, encouragement, or a pep talk

IMPORTANT DISTINCTIONS:
- "create a quiz" → tutor (it's a learning activity)
- "schedule a session" → scheduler (it's time planning)
- "I'm done" or "finished" or "that's all" → analyzer (implies wanting session review)
- "bye" at end of tutoring → analyzer (wrap up session)
- "yes" after scheduling question → scheduler (confirming scheduling)

CONVERSATION HISTORY:
{history_text}

CURRENT MESSAGE: "{user_message}"

Based on the full context, what is the user's intent?
Reply with ONE WORD only: tutor, scheduler, analyzer, or motivator"""

    response = llm.invoke([SystemMessage(content=prompt)])
    intent = response.content.strip().lower()

    # Validate and default to tutor if invalid
    if intent not in ["tutor", "scheduler", "analyzer", "motivator"]:
        return "tutor"

    return intent


# =============================================================================
# NODE 1: Intent Router - Figures out what the user wants
# =============================================================================

def intent_router_node(state: StudyPalState) -> dict:
    """
    Figure out what the user wants using ONLY LLM reasoning.

    This node analyzes the user's message and conversation context to decide:
    - Do they want tutoring help? → Go to tutor
    - Do they want to schedule? → Go to scheduler
    - Do they want to analyze their session? → Go to analyzer
    - Do they want motivation? → Go to motivator

    Args:
        state: The current workflow state

    Returns:
        Dictionary with updates to the state

    Example:
        Input: User says "What is a derivative?"
        Output: Sets next_agent = "tutor"
    """
    logger.info("🔀 Intent Router: Analyzing user request...")

    # If no messages yet, default to tutor
    if not state["messages"]:
        logger.info("   No messages yet, defaulting to tutor")
        return {
            "current_intent": "tutor",
            "next_agent": "tutor",
        }

    # Get last user message
    last_user_message = _get_last_human_message(state["messages"])
    if not last_user_message:
        logger.info("   No human message detected, ending turn")
        return {
            "current_intent": "tutor",
            "next_agent": "__end__",
        }

    user_text = last_user_message.content.strip()

    # Use LLM to classify intent (with full conversation context)
    logger.info("   Using LLM for classification...")
    intent = classify_intent_with_llm(user_text, state["messages"])
    logger.info(f"   Detected: {intent}")

    # Map intent to next_agent and state updates
    intent_map = {
        "tutor": {
            "current_intent": "tutor",
            "next_agent": "tutor",
            "session_mode": "active_tutoring",
            "tutor_session_active": True,
        },
        "scheduler": {
            "current_intent": "schedule",
            "next_agent": "scheduler",
            "session_mode": "scheduling_requested",
            "pending_schedule_request": user_text,
        },
        "analyzer": {
            "current_intent": "analyze",
            "next_agent": "analyzer",
            "session_mode": "analysis_requested",
            "tutor_session_active": False,
        },
        "motivator": {
            "current_intent": "motivate",
            "next_agent": "motivator",
            "needs_motivation": True,
            "session_mode": "motivation_requested",
        },
    }

    return intent_map.get(intent, intent_map["tutor"])


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
            "current_agent_avatar": get_agent_avatar("tutor"),
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

        conversation_history = ""
        recent_messages = state["messages"][-7:-1] if len(state["messages"]) > 1 else []
        if recent_messages:
            conversation_history = "\n\nRecent conversation:\n"
            for msg in recent_messages:
                role = "Student" if isinstance(msg, HumanMessage) else "Tutor"
                conversation_history += f"{role}: {msg.content}\n"

        system_message = f"""You are a friendly AI tutor assistant that teaches from the student's uploaded study materials.

CRITICAL RULES - YOU MUST FOLLOW THESE:
1. ONLY answer questions based on the provided context from study materials
2. EXCEPTIONS - You CAN respond naturally to these types of messages:
   - Greetings (e.g., "hello", "hi", "how are you?") → Reply warmly and ask if they're ready to study
   - Expressions of confusion (e.g., "I don't understand", "I'm lost") → Reassure them and offer simpler explanations
   - Motivation requests (e.g., "motivate me") → Encourage them briefly, then refocus on studying
3. For ALL other questions: If the context does NOT contain information to answer, you MUST say:
   "I cannot answer this question based on your study materials. Please ask about topics covered in your uploaded PDFs."
4. NEVER use your general knowledge for factual questions
5. NEVER hallucinate or invent facts not in the context
6. If you're unsure, say you don't have enough information in the materials

WHAT YOU CAN DO WHEN CONTEXT IS AVAILABLE:
- Answer questions based STRICTLY on the provided context
- Quote relevant parts from the context when possible
- Create quizzes based on the context
- Grade quiz answers based on the study materials
- Be encouraging and supportive about the material they're learning
- Use the recent conversation history to maintain context and continuity
- If context has formatting issues, interpret it as best you can

Student's name: {state.get('user_name', 'there')}

Remember: Your job is to help students learn ONLY from their uploaded materials. Be friendly for greetings and encouragement, but strict about staying on topic for actual learning content."""

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

    # Return state updates
    # The Intent Router will handle all routing decisions (including detecting "I'm done")
    return {
        "messages": [AIMessage(content=answer)],
        "tutor_session_active": True,
        "session_mode": "active_tutoring",
        "next_agent": "__end__",
        "current_agent_avatar": get_agent_avatar("tutor"),
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
                "current_agent_avatar": get_agent_avatar("scheduler"),
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
                "current_agent_avatar": get_agent_avatar("scheduler"),
            }

        message = "Just let me know with a simple \"yes\" or \"no\" if you'd like me to schedule your next session."
        return {
            "messages": [AIMessage(content=message)],
            "awaiting_schedule_confirmation": True,
            "awaiting_schedule_details": False,
            "pending_schedule_request": None,
            "user_wants_scheduling": False,
            "next_agent": "__end__",
            "current_agent_avatar": get_agent_avatar("scheduler"),
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
                "current_agent_avatar": get_agent_avatar("scheduler"),
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
                "current_agent_avatar": get_agent_avatar("scheduler"),
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
                    "current_agent_avatar": get_agent_avatar("scheduler"),
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
                    "current_agent_avatar": get_agent_avatar("scheduler"),
                }

    # Create scheduler
    calendar_connector = CalendarConnector()
    scheduler = SchedulerAgent(calendar_connector=calendar_connector)

    # === EXTRACT WEAK POINTS FROM ANALYZER ===
    # Get analysis results from state
    analysis_results = state.get("session_analysis") or state.get("analysis_results")
    stored_weak_points = state.get("weak_points")

    prioritized_recommendations = stored_weak_points
    if not prioritized_recommendations and analysis_results:
        if hasattr(analysis_results, "weak_points"):
            prioritized_recommendations = analysis_results.weak_points
        elif isinstance(analysis_results, dict) and "weak_points" in analysis_results:
            prioritized_recommendations = analysis_results["weak_points"]

    # === INJECT WEAK POINT TOPICS INTO USER INPUT IF NO SUBJECTS SPECIFIED ===
    # Check if user mentioned specific subjects
    has_subject_keywords = any(word in user_input.lower() for word in ["study", "focus", "subject", "topic"])

    # If no subjects mentioned AND we have weak points, inject them
    if not has_subject_keywords and prioritized_recommendations:
        weak_topics = []
        if hasattr(prioritized_recommendations, '__iter__'):
            # It's a list of WeakPoint objects or dicts
            for wp in prioritized_recommendations:
                if hasattr(wp, 'topic'):
                    weak_topics.append(wp.topic)
                elif isinstance(wp, dict) and 'topic' in wp:
                    weak_topics.append(wp['topic'])

        if weak_topics:
            # Add weak point topics to user input for scheduler parsing
            topics_str = ", ".join(weak_topics[:3])  # Use top 3 weak points
            user_input += f" studying {topics_str}"
            logger.info(f"   Injected weak point topics into schedule: {topics_str}")
        else:
            # Fallback: no weak points found
            user_input += " studying General Topics"
    elif not has_subject_keywords:
        # No subjects and no weak points - use generic fallback
        user_input += " studying General Topics"

    # Build context
    context = {
        "user_input": user_input,
        "user_id": state["user_id"]
    }

    try:
        # Generate schedule, use weak points if available
        schedule = scheduler.generate_schedule(
            context=context,
            recommendations=prioritized_recommendations
        )

        # Format nice response
        sessions = schedule.get("sessions", [])
        preferences = schedule.get("preferences", {})
        session_date = preferences.get("date")

        response = f"📚 I've created your study schedule!\n\n"

        # Show the date if available
        if session_date:
            from datetime import datetime
            try:
                date_obj = datetime.strptime(session_date, "%Y-%m-%d")
                day_name = date_obj.strftime("%A")
                formatted_date = date_obj.strftime("%B %d, %Y")
                response += f"📅 **{day_name}, {formatted_date}**\n\n"
            except (ValueError, TypeError):
                pass

        # === NEW: Reference analysis in scheduling response ===
        if analysis_results and hasattr(analysis_results, 'weak_points') and analysis_results.weak_points:
            weak_topics = [wp.topic for wp in analysis_results.weak_points[:3]]
            response += f"📊 Based on your session analysis, I've prioritized: {', '.join(weak_topics)}\n\n"

        study_sessions = [s for s in sessions if s['type'] == 'study']
        response += f"Found {len(study_sessions)} study sessions filling your entire time window:\n\n"

        session_number = 0
        for session in sessions:  # Show all sessions
            if session["type"] == "study":
                session_number += 1
                # Show task description if available, otherwise just subject
                task = session.get("task", session["subject"])
                # Show duration note if it's a partial session
                duration_note = session.get("duration_note", "")
                duration_text = f" ({duration_note})" if duration_note else ""
                response += f"{session_number}. 📖 {session['start']} - {session['end']}: {task}{duration_text}\n"
            elif session["type"] == "break":
                response += f"   ☕ {session['start']} - {session['end']}: Break\n"

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
            "current_agent_avatar": get_agent_avatar("scheduler"),
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
            "current_agent_avatar": get_agent_avatar("scheduler"),
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
            "current_agent_avatar": get_agent_avatar("analyzer"),
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
            "current_agent_avatar": get_agent_avatar("analyzer"),
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
            "current_agent_avatar": get_agent_avatar("analyzer"),
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
            "current_agent_avatar": get_agent_avatar("motivator"),
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
            "current_agent_avatar": get_agent_avatar("motivator"),
        }


# =============================================================================
# Conditional Routing Functions for Multi-Agent Orchestration
# =============================================================================

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
