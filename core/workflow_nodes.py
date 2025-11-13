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
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
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

    # Check if user is responding to a previous schedule offer
    has_existing_schedule = state.get("generated_schedule") is not None
    affirmative_words = ["yes", "yeah", "sure", "ok", "okay", "yep", "please", "sync"]
    is_affirmative = any(word == user_text.strip() or word in user_text.split() for word in affirmative_words)

    if any(word in user_text for word in ["schedule", "plan", "calendar", "studying"]) or has_time:
        intent = "schedule"
        next_node = "scheduler"
    elif has_existing_schedule and is_affirmative:
        # User is responding "yes" to sync the schedule
        intent = "schedule"
        next_node = "scheduler"
        logger.info("   Detected affirmative response to schedule sync")
    elif any(word in user_text for word in ["analyze", "session", "weak points", "finish", "review"]):
        intent = "analyze"
        next_node = "analyzer"
    elif any(word in user_text for word in ["motivat", "encourage", "inspiration"]):
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
    from core.rag_pipeline import get_rag_pipeline

    # Get the user-specific RAG pipeline instance
    # Each user has their own isolated ChromaDB collection to prevent
    # cross-contamination of study materials between users.
    user_id = state.get("user_id", "default_user")
    rag_pipeline = get_rag_pipeline(user_id=user_id)
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

        # Check if context is actually relevant to the question
        # This prevents the LLM from answering off-topic questions
        # Use a lightweight check - only block obviously off-topic questions
        # Keywords that indicate off-topic questions
        off_topic_keywords = [
            "recipe", "cooking", "weather", "sports", "movie", "music", "game",
            "restaurant", "travel", "shopping", "fashion", "celebrity", "joke"
        ]

        question_lower = question.lower()
        is_obviously_off_topic = any(keyword in question_lower for keyword in off_topic_keywords)

        if is_obviously_off_topic:
            # Quick keyword-based rejection for obviously off-topic questions
            logger.info("   🔍 Quick relevance check: OFF-TOPIC (keyword match)")
            answer = ("I don't have information about that in your study materials. "
                     "I'm here to help you learn from your uploaded PDFs. Please ask me about academic topics covered in your materials.")

            return {
                "messages": [AIMessage(content=answer)],
                "next_agent": "end"
            }

        # If not obviously off-topic, proceed with answering
        logger.info("   🔍 Relevance check: PASSED (proceeding to answer)")

        # Build conversation history for context (last 6 messages = 3 exchanges)
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

    # === NEW: Multi-turn tutoring support ===
    # Mark tutoring session as active (enables Tutor → Tutor loops)
    # The route_after_tutor function will decide if we continue or exit
    # based on user intent detection

    # Return state updates
    return {
        "messages": [AIMessage(content=answer)],
        "tutor_session_active": True,  # Enables multi-turn tutoring
        "session_mode": "active_tutoring",  # Tracks workflow state
        "next_agent": "tutor"  # Will be overridden by route_after_tutor conditional
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
                    "next_agent": "end"
                }
            except Exception as e:
                response = f"⚠️ I had trouble syncing to your calendar: {str(e)}\n\nYour schedule is still saved, but it wasn't added to your calendar."
                logger.error(f"   ❌ Calendar sync error: {e}")

                return {
                    "messages": [AIMessage(content=response)],
                    "next_agent": "end"
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
        analysis_results = state.get("analysis_results")
        weak_points = state.get("weak_points")

        # Generate schedule, use weak points if available
        schedule = scheduler.generate_schedule(
            context=context,
            recommendations=weak_points or analysis_results
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

        return {
            "messages": [AIMessage(content=response)],
            "generated_schedule": schedule,
            "session_mode": "scheduling_requested",
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

        # result is a SessionRecommendations dataclass object
        weak_points = result.weak_points

        if weak_points:
            response = f"📊 Session Analysis:\n\n"
            response += f"I identified {len(weak_points)} areas to focus on:\n\n"

            for idx, wp in enumerate(weak_points[:3], 1):
                topic = wp.topic
                difficulty = wp.difficulty_level
                icon = "🔴" if difficulty == "severe" else "🟡" if difficulty == "moderate" else "🟢"

                response += f"{idx}. {icon} {topic.upper()} - {difficulty} difficulty\n"

            response += "\nWould you like me to create a study schedule focusing on these topics?"
        else:
            response = "✅ Great session! No significant difficulties detected."

        logger.info(f"   ✓ Found {len(weak_points)} weak points")

        # === NEW: Detect scheduling intent for Analyzer → Scheduler handoff ===
        # Check if user explicitly requested scheduling in the conversation
        user_wants_scheduling = False

        # Look at last few user messages for scheduling keywords
        for msg in reversed(state["messages"][-5:]):
            if isinstance(msg, HumanMessage):
                user_text = msg.content.lower()
                scheduling_keywords = [
                    "schedule", "plan", "calendar", "study plan",
                    "when should i", "help me plan", "create a schedule"
                ]

                if any(keyword in user_text for keyword in scheduling_keywords):
                    user_wants_scheduling = True
                    logger.info(f"   🗓️  Detected scheduling request in: '{msg.content}'")
                    break

        return {
            "messages": [AIMessage(content=response)],
            "weak_points": result,
            "analysis_results": result,  # Store for scheduler to use
            "user_wants_scheduling": user_wants_scheduling,  # Flag for conditional routing
            "session_mode": "analysis_requested",
            "tutor_session_active": False,  # Tutoring session has ended
            "next_agent": "scheduler" if user_wants_scheduling else "end"
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
    from agents.user_profile import UserProfileStore
    from pathlib import Path

    try:
        # Load user profile store
        profile_store = UserProfileStore(Path("data/profiles"))

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

    # Check if workflow is explicitly marked complete
    if state.get("workflow_complete", False):
        logger.info("   → END (workflow_complete=True)")
        return "__end__"

    # Detect if user wants to exit tutoring session
    wants_to_exit = detect_tutor_exit_intent(state["messages"])

    if wants_to_exit:
        logger.info("   → ANALYZER (user wants to end session)")
        return "analyzer"
    else:
        logger.info("   → END (waiting for next user message)")
        return "__end__"


def route_after_analyzer(state: StudyPalState) -> str:
    """
    Conditional routing after analyzer agent completes.

    Decides where to go after analysis:
    - To "scheduler" if user wants scheduling (Analyzer → Scheduler)
    - To END if no scheduling requested

    This enables automatic handoff from analysis to scheduling when appropriate.

    Args:
        state: Current workflow state

    Returns:
        str: Next node name ("scheduler" or "__end__")

    Flow Logic:
        1. Check user_wants_scheduling flag → "scheduler"
        2. Check for scheduling keywords in last message → "scheduler"
        3. Otherwise → END
    """
    logger.info("🔀 Routing after Analyzer...")

    # Check explicit scheduling flag
    if state.get("user_wants_scheduling", False):
        logger.info("   → SCHEDULER (user_wants_scheduling=True)")
        return "scheduler"

    # Check last message for scheduling intent
    if state["messages"]:
        last_message = state["messages"][-1]
        if isinstance(last_message, HumanMessage):
            user_text = last_message.content.lower()
            scheduling_keywords = ["schedule", "plan", "calendar", "study plan", "when should i"]

            if any(keyword in user_text for keyword in scheduling_keywords):
                logger.info(f"   → SCHEDULER (detected scheduling keywords in: '{user_text}')")
                return "scheduler"

    logger.info("   → END (no scheduling requested)")
    return "__end__"
