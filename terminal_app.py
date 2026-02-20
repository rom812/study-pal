"""
Simple terminal-based Study Pal (no Gradio needed).
Run this if Gradio is causing issues.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment
load_dotenv()

# Setup logging
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Create log filename with timestamp
log_filename = logs_dir / f"terminal_app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_filename), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

print("=" * 70)
print("  🎓 STUDY PAL - Terminal Interface")
print("=" * 70)
print(f"\n📝 Logging to: {log_filename}")
print("\nInitializing chatbot...")
logger.info("Starting Study Pal Terminal Interface")

try:
    logger.info("Importing LangGraphChatbot...")
    from core.langgraph_chatbot import LangGraphChatbot

    logger.info("✓ Import successful")

    # Create chatbot instance
    user_id = input("\nEnter your username (or press Enter for 'demo_user'): ").strip() or "demo_user"
    logger.info(f"Creating chatbot for user: {user_id}")
    chatbot = LangGraphChatbot(user_id=user_id, session_id=user_id)
    logger.info(f"✓ Chatbot initialized for user: {user_id}")

    print(f"\n✅ Chatbot initialized for user: {user_id}")
    print("\nCommands:")
    print("  - Type your question or message")
    print("  - Type 'upload' to upload a PDF")
    print("  - Type 'clear' to clear conversation")
    print("  - Type 'quit' or 'exit' to exit")
    print("\n" + "=" * 70 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "q"]:
                logger.info("User requested exit")
                print("\n👋 Goodbye!")
                break

            if user_input.lower() == "clear":
                logger.info("Clearing conversation")
                result = chatbot.clear_conversation()
                logger.info(f"Conversation cleared: {result}")
                print(f"\n✅ {result}\n")
                continue

            if user_input.lower() == "upload":
                file_path = input("Enter path to PDF file: ").strip()
                logger.info(f"Upload requested: {file_path}")
                if os.path.exists(file_path):
                    try:
                        result = chatbot.ingest_material(Path(file_path))
                        count = chatbot.get_materials_count()
                        logger.info(f"Upload successful: {result}, Total chunks: {count}")
                        print(f"\n✅ {result}")
                        print(f"📊 Total chunks: {count}\n")
                    except Exception as e:
                        logger.error(f"Upload failed: {e}", exc_info=True)
                        print(f"\n❌ Error uploading file: {e}\n")
                else:
                    logger.warning(f"File not found: {file_path}")
                    print(f"\n❌ File not found: {file_path}\n")
                continue

            # Regular chat
            logger.info(f"User message: {user_input}")
            print("\n🤖 ", end="", flush=True)
            response = chatbot.chat(user_input)
            logger.info(f"Bot response: {response[:100]}...")
            print(f"{response}\n")

        except KeyboardInterrupt:
            logger.info("User interrupted (Ctrl+C)")
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            logger.info("No more input (EOF)")
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error during chat: {e}", exc_info=True)
            print(f"\n❌ Error: {e}\n")

except Exception as e:
    logger.error(f"Failed to initialize chatbot: {e}", exc_info=True)
    print(f"\n❌ Failed to initialize chatbot: {e}")
    print("\nPlease check:")
    print("  1. Your .env file has OPENAI_API_KEY")
    print("  2. All dependencies are installed: pip install -r requirements.txt")
    print(f"\n📝 Check logs for details: {log_filename}")
    exit(1)
