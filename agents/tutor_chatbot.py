"""Interactive chatbot that combines TutorAgent with conversational AI."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from langchain.memory import ConversationBufferWindowMemory
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
    model_name: str = "gpt-4"
    temperature: float = 0.7
    memory_k: int = 10  # Number of exchanges to remember

    # These will be initialized in __post_init__
    memory: ConversationBufferWindowMemory = field(init=False)
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

        # Initialize LangChain memory (sliding window)
        self.memory = ConversationBufferWindowMemory(
            k=self.memory_k,
            return_messages=True,
            memory_key="history",
        )

        print(f"[chatbot] Initialized with model: {self.model_name}")
        print(f"[chatbot] Memory: last {self.memory_k} exchanges")

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

        # Get chat history from memory
        chat_history = self.memory.load_memory_variables({})

        # Build messages for LLM
        messages = [SystemMessage(content=system_prompt)]

        # Add chat history if available
        if chat_history and "history" in chat_history:
            messages.extend(chat_history["history"])

        # Add current user message
        messages.append(HumanMessage(content=user_message))

        # Generate response
        try:
            response = self.llm.invoke(messages)
            assistant_message = response.content

            # Save interaction to memory (LangChain handles this automatically)
            self.memory.save_context(
                {"input": user_message}, {"output": assistant_message}
            )

            return assistant_message

        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            # Still save error to memory to maintain conversation flow
            self.memory.save_context({"input": user_message}, {"output": error_msg})
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
        chat_history = self.memory.load_memory_variables({})
        if chat_history and "history" in chat_history:
            num_messages = len(chat_history["history"])
            return f"Conversation: {num_messages} messages in memory window"
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
            "You are a helpful AI tutor assistant. Your role is to help students "
            "understand study materials by answering their questions clearly and accurately.\n\n"
            "Guidelines:\n"
            "- Use the provided context from study materials when available\n"
            "- If context is relevant, base your answer on it\n"
            "- If context is not sufficient, acknowledge this and provide general guidance\n"
            "- Be encouraging and supportive\n"
            "- Break down complex topics into understandable parts\n"
            "- Ask clarifying questions if needed\n"
        )

        if context_chunks:
            context_text = "\n\n".join(
                f"[Context {i+1}]:\n{chunk}" for i, chunk in enumerate(context_chunks)
            )
            return f"{base_prompt}\n\nRELEVANT CONTEXT FROM STUDY MATERIALS:\n{context_text}"
        else:
            return f"{base_prompt}\n\nNote: No relevant context found in study materials for this question."


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
        print("\n💬 Just type naturally to chat!")

    def _print_status(self) -> None:
        """Print system status."""
        print("\n📊 System Status:")
        print(f"  Model: {self.chatbot.model_name}")
        print(f"  Temperature: {self.chatbot.temperature}")
        print(f"  Knowledge base: {self.chatbot.get_materials_count()} chunks")
        print(f"  {self.chatbot.get_conversation_summary()}")