"""Interactive chatbot that combines TutorAgent with conversational AI."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agents.tutor_agent import TutorAgent


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
    model_name: str = "gpt-4o"
    temperature: float = 0.7
    memory_k: int = 20  # Number of messages to remember (10 exchanges)

    # These will be initialized in __post_init__
    memory: ChatMessageHistory = field(init=False)
    llm: ChatOpenAI = field(init=False)

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
        print("[chatbot] Cost-optimized: Using gpt-4o-mini for 98% cost savings")

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
            "2. If the context does NOT contain information to answer the question and also the student doesn't ask a general question like: 'what can u teach me?' or 'hello how are you' (these kind of questions you can answer and be polite) else:, you MUST say\n"
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
            context_text = "\n\n".join(f"[Context {i + 1}]:\n{chunk}" for i, chunk in enumerate(context_chunks))
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
        print("\n💬 Natural Language (LangGraph Multi-Agent System):")
        print("  Just chat naturally! The system automatically routes to the right agent:")
        print("  • 'What is [topic]?'              → Tutor agent (Q&A)")
        print("  • 'Analyze my weak points'        → Analyzer agent")
        print("  • 'Create a study schedule...'    → Scheduler agent")
        print("  • 'I need motivation'             → Motivator agent")
        print("\n✨ No slash commands needed - just describe what you need!")

    def _print_status(self) -> None:
        """Print system status."""
        print("\n📊 System Status:")

        # Check if this is LangGraph chatbot or legacy chatbot
        from core.langgraph_chatbot import LangGraphChatbot

        if isinstance(self.chatbot, LangGraphChatbot):
            print("  Mode: LangGraph Multi-Agent System")
            print(f"  User ID: {self.chatbot.user_id}")
            print(f"  Knowledge base: {self.chatbot.get_materials_count()} chunks")
            print(f"  {self.chatbot.get_conversation_summary()}")

            # Show last detected intent
            last_intent = self.chatbot.get_last_intent()
            if last_intent != "unknown":
                print(f"  Last detected intent: {last_intent}")
        else:
            # Legacy TutorChatbot
            print("  Mode: Legacy Chatbot")
            print(f"  Model: {self.chatbot.model_name}")
            print(f"  Temperature: {self.chatbot.temperature}")
            print(f"  Knowledge base: {self.chatbot.get_materials_count()} chunks")
            print(f"  {self.chatbot.get_conversation_summary()}")
