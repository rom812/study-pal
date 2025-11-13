"""
Terminal-based Test Interface for LangGraph Workflow

A lightweight command-line interface to test the multi-agent system
without the overhead of Gradio.

Usage:
    python test_terminal.py

Commands:
    chat <message>  - Send a message to the chatbot
    upload <path>   - Upload a PDF file
    status          - Show workflow status
    clear           - Clear conversation history
    quit/exit       - Exit the program
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_terminal.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import after logging is configured
from core.langgraph_chatbot import LangGraphChatbot


class TerminalSimulator:
    """Simple terminal interface for testing the chatbot."""

    def __init__(self, user_id: str = "terminal_user"):
        """Initialize the terminal simulator."""
        self.user_id = user_id
        self.chatbot = None
        print("\n" + "=" * 80)
        print("  🧪 STUDY PAL - TERMINAL TEST INTERFACE")
        print("=" * 80)
        print("\n⏳ Initializing chatbot (this may take a moment)...")

        try:
            self.chatbot = LangGraphChatbot(user_id=user_id, session_id=user_id)
            print("✅ Chatbot initialized successfully!\n")
        except Exception as e:
            print(f"❌ Error initializing chatbot: {e}\n")
            raise

    def print_help(self):
        """Print help message."""
        print("\n📖 Available Commands:")
        print("  chat <message>  - Chat with the AI (e.g., 'chat What is calculus?')")
        print("  upload <path>   - Upload a PDF file (e.g., 'upload materials/calculus.pdf')")
        print("  status          - Show current workflow status")
        print("  clear           - Clear conversation history")
        print("  help            - Show this help message")
        print("  quit/exit       - Exit the simulator")
        print("\n💡 Quick Test:")
        print("  Just type your message directly (no 'chat' prefix needed)")
        print("  Example: 'What is machine learning?'\n")

    def chat(self, message: str):
        """Send a chat message."""
        if not message.strip():
            print("❌ Please provide a message.\n")
            return

        print(f"\n👤 You: {message}")
        print("🤖 AI: ", end="", flush=True)

        try:
            response = self.chatbot.chat(message)
            print(f"{response}\n")
        except Exception as e:
            logger.error(f"Chat error: {e}", exc_info=True)
            print(f"❌ Error: {e}\n")

    def upload(self, file_path: str):
        """Upload a PDF file."""
        if not file_path:
            print("❌ Please provide a file path.\n")
            return

        path = Path(file_path)
        if not path.exists():
            print(f"❌ File not found: {file_path}\n")
            return

        if path.suffix.lower() != '.pdf':
            print(f"❌ Only PDF files are supported. Got: {path.suffix}\n")
            return

        print(f"📤 Uploading {path.name}...")

        try:
            result = self.chatbot.ingest_material(path)
            print(f"✅ {result}\n")
        except Exception as e:
            logger.error(f"Upload error: {e}", exc_info=True)
            print(f"❌ Error: {e}\n")

    def show_status(self):
        """Show current workflow status."""
        try:
            materials_count = self.chatbot.get_materials_count()
            conversation_summary = self.chatbot.get_conversation_summary()
            state = self.chatbot.conversation_state

            print("\n" + "=" * 80)
            print("📊 WORKFLOW STATUS")
            print("=" * 80)
            print(f"\n👤 User ID: {self.user_id}")
            print(f"📚 Knowledge Base: {materials_count} document chunks")
            print(f"💬 {conversation_summary}")

            session_mode = state.get("session_mode", "None")
            tutor_active = state.get("tutor_session_active", False)
            has_analysis = state.get("analysis_results") is not None
            wants_scheduling = state.get("user_wants_scheduling", False)

            print("\n🔄 Workflow State:")
            print(f"  • Session Mode: {session_mode}")
            print(f"  • Tutor Loop Active: {'✅' if tutor_active else '❌'}")
            print(f"  • Has Analysis Results: {'✅' if has_analysis else '❌'}")
            print(f"  • Scheduling Requested: {'✅' if wants_scheduling else '❌'}")

            print("\n✨ Workflow Capabilities:")
            print("  • Multi-turn tutoring (Tutor → Tutor loops)")
            print("  • Auto-analysis (Tutor → Analyzer on exit)")
            print("  • Auto-scheduling (Analyzer → Scheduler)")
            print("  • Direct routing to all agents")
            print("=" * 80 + "\n")
        except Exception as e:
            logger.error(f"Status error: {e}", exc_info=True)
            print(f"❌ Error getting status: {e}\n")

    def clear_conversation(self):
        """Clear conversation history."""
        try:
            result = self.chatbot.clear_conversation()
            print(f"✅ {result}\n")
        except Exception as e:
            logger.error(f"Clear error: {e}", exc_info=True)
            print(f"❌ Error: {e}\n")

    def process_command(self, user_input: str) -> bool:
        """
        Process a user command.

        Returns:
            False if user wants to quit, True otherwise
        """
        user_input = user_input.strip()

        if not user_input:
            return True

        # Handle quit commands
        if user_input.lower() in ['quit', 'exit', 'q']:
            return False

        # Handle help
        if user_input.lower() in ['help', '?']:
            self.print_help()
            return True

        # Parse command
        parts = user_input.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Execute command
        if command == 'chat':
            self.chat(args)
        elif command == 'upload':
            self.upload(args)
        elif command == 'status':
            self.show_status()
        elif command == 'clear':
            self.clear_conversation()
        else:
            # Treat the entire input as a chat message
            self.chat(user_input)

        return True

    def run(self):
        """Run the interactive terminal loop."""
        print("=" * 80)
        print("  🚀 READY TO TEST!")
        print("=" * 80)
        print("\n💡 Type 'help' for commands, or just start chatting!\n")

        # Check for OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  WARNING: OPENAI_API_KEY not found in environment!")
            print("   Make sure you have a .env file with your API key.\n")

        try:
            while True:
                try:
                    user_input = input(">>> ")
                    if not self.process_command(user_input):
                        break
                except KeyboardInterrupt:
                    print("\n\n👋 Interrupted by user. Type 'quit' to exit or continue chatting.\n")
                    continue
                except EOFError:
                    break
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            print(f"\n❌ Fatal error: {e}")
        finally:
            print("\n👋 Thanks for testing! Check logs/test_terminal.log for details.\n")


def main():
    """Main entry point."""
    try:
        simulator = TerminalSimulator()
        simulator.run()
    except Exception as e:
        logger.error(f"Failed to start simulator: {e}", exc_info=True)
        print(f"\n❌ Failed to start: {e}")
        print("Check logs/test_terminal.log for details.\n")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
