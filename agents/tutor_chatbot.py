"""Interactive chatbot that combines TutorAgent with conversational AI."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

from agents.tutor_agent import TutorAgent
from agents.weakness_detector_agent import WeaknessDetectorAgent
from core.weakness_analyzer import SessionRecommendations, WeakPoint


@dataclass
class TutorChatbot:
    """
    Interactive chatbot that combines RAG-based tutoring with conversation memory.

    Uses LangChain's built-in memory for conversation tracking:
    - ConversationBufferWindowMemory for sliding window context
    - Automatic message history management
    - Integration with LangChain chains

    Features:
    - Remembers conversation history (last 10 messages)
    - Retrieves relevant context from study materials
    - Uses GPT-4 for natural responses
    - Maintains conversation flow

    Example:
        chatbot = TutorChatbot(tutor_agent=tutor)
        response = chatbot.chat("What is a derivative?")
        print(response)
    """

    tutor_agent: TutorAgent
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.7
    memory_k: int = 20  # Number of messages to remember (10 exchanges)

    # These will be initialized in __post_init__
    memory: ChatMessageHistory = field(init=False)
    llm: ChatOpenAI = field(init=False)
    last_recommendations: SessionRecommendations | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize the chatbot components."""
        # Initialize OpenAI LLM
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            openai_api_key=api_key,
        )

        # Initialize LangChain memory
        self.memory = ChatMessageHistory()

        print(f"[chatbot] Initialized with model: {self.model_name}")
        print(f"[chatbot] Memory: last {self.memory_k // 2} exchanges")
        print(f"[chatbot] Cost-optimized: Using gpt-4o-mini for 98% cost savings")

    def chat(self, user_message: str, k: int = 3) -> str:
        """
        Process user message and generate response with RAG context.

        Args:
            user_message: User's input message
            k: Number of context chunks to retrieve

        Returns:
            Assistant's response
        """
        # Retrieve relevant context from study materials
        context_chunks = self.tutor_agent.get_context(user_message, k=k)

        # Build system prompt with context
        system_prompt = self._build_system_prompt(context_chunks)

        # Build messages for LLM
        messages = [SystemMessage(content=system_prompt)]

        # Add chat history (keep only last N messages for sliding window)
        history_messages = self.memory.messages
        if len(history_messages) > self.memory_k:
            history_messages = history_messages[-self.memory_k :]

        messages.extend(history_messages)

        # Add current user message
        messages.append(HumanMessage(content=user_message))

        # Generate response
        try:
            response = self.llm.invoke(messages)
            assistant_message = response.content

            # Save interaction to memory
            self.memory.add_user_message(user_message)
            self.memory.add_ai_message(assistant_message)

            return assistant_message

        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            # Still save error to memory to maintain conversation flow
            self.memory.add_user_message(user_message)
            self.memory.add_ai_message(error_msg)
            return error_msg

    def ingest_material(self, path: Path) -> str:
        """
        Ingest study material and return status message.

        Args:
            path: Path to PDF file

        Returns:
            Status message
        """
        try:
            num_chunks = self.tutor_agent.ingest_material(path)
            return f"Successfully ingested {path.name} ({num_chunks} chunks)"
        except FileNotFoundError:
            return f"Error: File not found: {path}"
        except ValueError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error ingesting file: {e}"

    def get_materials_count(self) -> int:
        """Get number of document chunks in knowledge base."""
        return self.tutor_agent.count_materials()

    def clear_conversation(self) -> str:
        """Clear conversation history."""
        self.memory.clear()
        return "Conversation history cleared."

    def clear_materials(self) -> str:
        """Clear all study materials."""
        self.tutor_agent.clear_materials()
        return "All study materials cleared from knowledge base."

    def get_conversation_summary(self) -> str:
        """Get summary of current conversation."""
        num_messages = len(self.memory.messages)
        if num_messages > 0:
            num_exchanges = num_messages // 2
            return f"Conversation: {num_messages} messages ({num_exchanges} exchanges)"
        return "Conversation: No messages yet"

    def analyze_session(self, session_topic: str | None = None) -> SessionRecommendations:
        """
        Analyze the current tutoring session to identify weak points and generate recommendations.

        Args:
            session_topic: Optional topic that was studied during the session

        Returns:
            SessionRecommendations with weak points and study suggestions
        """
        # Use the weakness detector agent for LLM-based analysis
        detector = WeaknessDetectorAgent(model="gpt-4o-mini")
        result = detector.analyze_conversation(self.memory.messages, session_topic=session_topic)

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
        from core.weakness_analyzer import RecommendationBuilder

        # Generate recommendations using the builder's helper methods
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

        return recommendations

    def _build_system_prompt(self, context_chunks: list[str]) -> str:
        """
        Build system prompt with RAG context.

        Args:
            context_chunks: Retrieved context from vector store

        Returns:
            System prompt string
        """
        base_prompt = (
            "You are a strict AI tutor assistant. Your role is to help students "
            "understand ONLY their study materials.\n\n"
            "CRITICAL RULES - YOU MUST FOLLOW THESE:\n"
            "1. ONLY answer questions based on the provided context from study materials\n"
            "2. If the context does NOT contain information to answer the question, you MUST say:\n"
            "   'I cannot answer this question based on your study materials. Please ask about topics covered in your uploaded PDFs.'\n"
            "3. NEVER use your general knowledge or make up information\n"
            "4. NEVER hallucinate or invent facts not in the context\n"
            "5. If you're unsure, say you don't have enough information in the materials\n\n"
            "Guidelines when context IS available:\n"
            "- Base your answer STRICTLY on the provided context\n"
            "- Quote relevant parts from the context when possible\n"
            "- Be encouraging and supportive\n"
            "- Break down complex topics into understandable parts\n"
        )

        if context_chunks:
            context_text = "\n\n".join(
                f"[Context {i+1}]:\n{chunk}" for i, chunk in enumerate(context_chunks)
            )
            return (
                f"{base_prompt}\n\n"
                f"RELEVANT CONTEXT FROM STUDY MATERIALS:\n{context_text}\n\n"
                f"Remember: Answer ONLY based on the above context. If the answer is not in the context, "
                f"clearly state that the information is not available in the study materials."
            )
        else:
            return (
                f"{base_prompt}\n\n"
                f"⚠️ NO CONTEXT AVAILABLE\n"
                f"No relevant information was found in the study materials.\n"
                f"You MUST tell the user that you cannot answer this question based on their uploaded materials."
            )


@dataclass
class ChatInterface:
    """
    Command-line interface for the TutorChatbot.

    Provides an interactive chat loop with commands:
    - /help: Show available commands
    - /ingest <path>: Load a PDF file
    - /count: Show materials count
    - /clear: Clear conversation history
    - /clear-materials: Clear all study materials
    - /status: Show system status
    - /quit or /exit: Exit the chatbot
    """

    chatbot: TutorChatbot

    def run(self) -> None:
        """Start the interactive chat loop."""
        self._print_welcome()

        while True:
            try:
                # Get user input
                user_input = input("\n💭 You: ").strip()

                if not user_input:
                    continue

                # Check for commands
                if user_input.startswith("/"):
                    should_continue = self._handle_command(user_input)
                    if not should_continue:
                        break
                    continue

                # Regular chat message
                print("\n🎓 Tutor: ", end="", flush=True)
                response = self.chatbot.chat(user_input)
                print(response)

            except KeyboardInterrupt:
                print("\n\nGoodbye! Happy studying! 📚")
                break
            except EOFError:
                print("\n\nGoodbye! Happy studying! 📚")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")

    def _handle_command(self, command: str) -> bool:
        """
        Handle slash commands.

        Args:
            command: Command string (starts with /)

        Returns:
            True to continue, False to exit
        """
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd in ["/quit", "/exit"]:
            print("\n👋 Goodbye! Happy studying! 📚")
            return False

        elif cmd == "/help":
            self._print_help()

        elif cmd == "/ingest":
            if not args:
                print("❌ Usage: /ingest <path_to_pdf>")
            else:
                path = Path(args.strip())
                print(f"📚 Ingesting {path.name}...")
                result = self.chatbot.ingest_material(path)
                print(f"✓ {result}")

        elif cmd == "/count":
            count = self.chatbot.get_materials_count()
            print(f"📊 Knowledge base: {count} document chunks")

        elif cmd == "/clear":
            result = self.chatbot.clear_conversation()
            print(f"🧹 {result}")

        elif cmd == "/clear-materials":
            confirm = input("⚠️  Clear all materials? (yes/no): ").strip().lower()
            if confirm == "yes":
                result = self.chatbot.clear_materials()
                print(f"🧹 {result}")
            else:
                print("Cancelled.")

        elif cmd == "/status":
            self._print_status()

        elif cmd == "/finish":
            self._handle_finish_session()

        elif cmd == "/schedule":
            self._handle_schedule_creation()

        else:
            print(f"❌ Unknown command: {cmd}")
            print("💡 Type /help for available commands")

        return True

    def _print_welcome(self) -> None:
        """Print welcome message."""
        print("\n" + "=" * 60)
        print("🎓 Welcome to Study Pal Tutor Chatbot!")
        print("=" * 60)
        print("\nI'm your AI study assistant. I can help you understand")
        print("your study materials and answer questions.")
        print("\n💡 Tips:")
        print("  - Use /ingest <pdf_path> to load study materials")
        print("  - Ask me questions about your materials")
        print("  - Type /help to see all commands")
        print("  - Type /quit to exit")
        print("\n" + "=" * 60)

    def _print_help(self) -> None:
        """Print help information."""
        print("\n📖 Available Commands:")
        print("  /help                  - Show this help message")
        print("  /ingest <path>        - Load a PDF file into knowledge base")
        print("  /count                - Show number of chunks in knowledge base")
        print("  /status               - Show system status")
        print("  /clear                - Clear conversation history")
        print("  /clear-materials      - Clear all study materials")
        print("  /quit or /exit        - Exit the chatbot")
        print("\n💬 Natural Language Commands (with LangGraph):")
        print("  'What is [topic]?'              - Ask tutoring questions")
        print("  'Schedule my study time...'     - Create study schedules")
        print("  'Analyze my weak points'        - Get session analysis")
        print("  'I need motivation'             - Get motivational messages")
        print("\n✨ Just chat naturally - the system figures out what you need!")

    def _print_status(self) -> None:
        """Print system status."""
        print("\n📊 System Status:")

        # Check if this is LangGraph chatbot or legacy chatbot
        from core.langgraph_chatbot import LangGraphChatbot

        if isinstance(self.chatbot, LangGraphChatbot):
            print(f"  Mode: LangGraph Multi-Agent System")
            print(f"  User ID: {self.chatbot.user_id}")
            print(f"  Knowledge base: {self.chatbot.get_materials_count()} chunks")
            print(f"  {self.chatbot.get_conversation_summary()}")

            # Show last detected intent
            last_intent = self.chatbot.get_last_intent()
            if last_intent != "unknown":
                print(f"  Last detected intent: {last_intent}")
        else:
            # Legacy TutorChatbot
            print(f"  Mode: Legacy Chatbot")
            print(f"  Model: {self.chatbot.model_name}")
            print(f"  Temperature: {self.chatbot.temperature}")
            print(f"  Knowledge base: {self.chatbot.get_materials_count()} chunks")
            print(f"  {self.chatbot.get_conversation_summary()}")

    def _handle_finish_session(self) -> None:
        """Analyze the session and display recommendations."""
        num_messages = len(self.chatbot.memory.messages)

        if num_messages < 2:
            print("\n⚠️  Not enough conversation to analyze.")
            print("   Have at least one exchange before finishing the session.")
            return

        print("\n🔍 Analyzing your study session...")

        # Ask for optional session topic
        session_topic = input("What topic did you study? (optional, press Enter to skip): ").strip()
        if not session_topic:
            session_topic = None

        # Analyze the session
        recommendations = self.chatbot.analyze_session(session_topic=session_topic)

        # Display results
        self._display_session_analysis(recommendations)

    def _display_session_analysis(self, recommendations: SessionRecommendations) -> None:
        """Display session analysis results in a user-friendly format."""
        print("\n" + "=" * 70)
        print("📊 Session Analysis Report")
        print("=" * 70)

        # Session summary
        print(f"\n📝 {recommendations.session_summary}")

        # Weak points
        if recommendations.weak_points:
            print(f"\n🎯 Areas for Improvement ({len(recommendations.weak_points)} identified):")
            print("-" * 70)

            for idx, wp in enumerate(recommendations.weak_points, 1):
                # Difficulty indicator
                if wp.difficulty_level == "severe":
                    icon = "🔴"
                elif wp.difficulty_level == "moderate":
                    icon = "🟡"
                else:
                    icon = "🟢"

                print(f"\n{idx}. {icon} {wp.topic.upper()} - {wp.difficulty_level.capitalize()} difficulty")
                print(f"   Frequency: {wp.frequency} mentions")
                if wp.confusion_indicators > 0:
                    print(f"   Confusion signals detected: {wp.confusion_indicators}")

                # Show evidence
                if wp.evidence:
                    print(f"   Example: \"{wp.evidence[0][:80]}...\"" if len(wp.evidence[0]) > 80 else f"   Example: \"{wp.evidence[0]}\"")

        else:
            print("\n✅ Great session! No significant difficulties detected.")

        # Priority topics
        if recommendations.priority_topics:
            print(f"\n🎯 Priority Topics for Next Session:")
            for idx, topic in enumerate(recommendations.priority_topics[:3], 1):
                print(f"   {idx}. {topic}")

        # Suggested focus time
        if recommendations.suggested_focus_time:
            print(f"\n⏱️  Suggested Study Time:")
            for topic, minutes in list(recommendations.suggested_focus_time.items())[:3]:
                print(f"   • {topic}: {minutes} minutes")

        # Study tips
        if recommendations.study_approach_tips:
            print(f"\n💡 Study Recommendations:")
            for idx, tip in enumerate(recommendations.study_approach_tips, 1):
                print(f"   {idx}. {tip}")

        print("\n" + "=" * 70)
        print("Keep up the great work! 🚀")
        print("=" * 70 + "\n")

    def _handle_schedule_creation(self) -> None:
        """Create tomorrow's study schedule based on session analysis."""
        from agents.scheduler_agent import SchedulerAgent
        from core.mcp_connectors import CalendarConnector

        # Check if we have recommendations from /finish
        if self.chatbot.last_recommendations is None:
            print("\n⚠️  No session analysis available.")
            print("   Run /finish first to analyze your study session, then use /schedule.")
            return

        print("\n📅 Creating Tomorrow's Study Schedule")
        print("=" * 70)

        # Ask for availability
        print("\nWhen are you available to study tomorrow?")
        start_time = input("Start time (HH:MM, 24-hour format): ").strip()
        end_time = input("End time (HH:MM, 24-hour format): ").strip()

        if not start_time or not end_time:
            print("❌ Both start and end times are required.")
            return

        # Build context for scheduler
        context = {
            "user_input": f"I'm available from {start_time} to {end_time}. "
            f"Topics: {', '.join(self.chatbot.last_recommendations.priority_topics[:5])}"
        }

        try:
            # Create scheduler with calendar connector
            calendar_connector = CalendarConnector()
            scheduler = SchedulerAgent(calendar_connector=calendar_connector)
            schedule = scheduler.generate_schedule(
                context=context, recommendations=self.chatbot.last_recommendations
            )

            # Display the schedule
            self._display_schedule(schedule)

            # Ask if user wants to sync to calendar
            sync_choice = input("\n📆 Sync this schedule to your calendar? (yes/no): ").strip().lower()
            if sync_choice in ["yes", "y"]:
                try:
                    scheduler.sync_schedule(schedule)
                    print("✅ Schedule synced to calendar!")
                except Exception as e:
                    print(f"⚠️  Could not sync to calendar: {e}")
                    print("   (Calendar integration may not be configured)")

        except ValueError as e:
            print(f"\n❌ Error creating schedule: {e}")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")

    def _display_schedule(self, schedule: dict) -> None:
        """Display the generated study schedule."""
        print("\n" + "=" * 70)
        print("📋 Tomorrow's Study Schedule")
        print("=" * 70)

        preferences = schedule.get("preferences", {})
        sessions = schedule.get("sessions", [])
        based_on_weak_points = schedule.get("based_on_weak_points", False)

        # Show if schedule is based on weak points
        if based_on_weak_points:
            print("\n✨ This schedule prioritizes your weak points!")
            if preferences.get("severe_topics"):
                print(f"   🔴 High priority: {', '.join(preferences['severe_topics'])}")
            if preferences.get("moderate_topics"):
                print(f"   🟡 Medium priority: {', '.join(preferences['moderate_topics'])}")

        # Display sessions
        print(f"\n📚 Study Sessions ({len([s for s in sessions if s['type'] == 'study'])} Pomodoro blocks):")
        print("-" * 70)

        for idx, session in enumerate(sessions, 1):
            if session["type"] == "study":
                subject = session["subject"]
                start = session["start"]
                end = session["end"]
                print(f"{idx:2}. 📖 {start} - {end}  |  {subject}")
            else:
                start = session["start"]
                end = session["end"]
                print(f"    ☕ {start} - {end}  |  Break")

        print("=" * 70)