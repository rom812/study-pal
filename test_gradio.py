"""
Test Gradio UI for Enhanced LangGraph Workflow

This is a simplified, single-chatbot interface that demonstrates the enhanced
multi-agent orchestration workflow. No tabs needed - the intent router automatically
handles all requests:

- Study questions → Tutor Agent (with multi-turn loops)
- Schedule requests → Scheduler Agent
- Session analysis → Analyzer Agent (with auto-scheduling)
- Motivation → Motivator Agent

The workflow automatically handles:
- Tutor → Tutor loops (multi-turn conversations)
- Tutor → Analyzer → Scheduler pipelines
- All agent collaboration and state propagation
"""

import os
import logging
from pathlib import Path
import gradio as gr
from dotenv import load_dotenv

from core.langgraph_chatbot import LangGraphChatbot

# Load environment variables
load_dotenv()

# Configure logging
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_gradio.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global chatbot instances
chatbot_instances = {}


def get_or_create_chatbot(user_id: str = "test_user") -> LangGraphChatbot:
    """Get or create a chatbot instance for a user."""
    if user_id not in chatbot_instances:
        chatbot_instances[user_id] = LangGraphChatbot(user_id=user_id, session_id=user_id)
    return chatbot_instances[user_id]


def upload_file(file, user_id: str = "test_user"):
    """Handle file upload and ingestion."""
    if file is None:
        return "❌ Please upload a file first.", "📚 No materials loaded"

    try:
        chatbot = get_or_create_chatbot(user_id)

        # Get the file path from the upload
        file_path = Path(file)

        # Ingest the material
        result = chatbot.ingest_material(file_path)

        # Get updated count
        count = chatbot.get_materials_count()

        return (
            f"✅ {result}",
            f"📚 Knowledge base: {count} chunks loaded"
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return f"❌ Error: {str(e)}\n\n{error_details}", "📚 Error loading materials"


def chat_with_agents(message, history, user_id: str = "test_user"):
    """
    Handle chat messages with the enhanced multi-agent system.

    The LangGraph workflow automatically:
    1. Routes to the correct agent via Intent Router
    2. Handles multi-turn tutoring loops (Tutor → Tutor)
    3. Manages agent handoffs (Tutor → Analyzer → Scheduler)
    4. Propagates state between agents
    """
    if not message.strip():
        return history, ""

    try:
        chatbot = get_or_create_chatbot(user_id)

        # Get response from enhanced LangGraph workflow
        # The workflow handles all routing and orchestration automatically
        response = chatbot.chat(message)

        # Update history
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": response})

        return history, ""
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        error_msg = f"❌ Error: {str(e)}\n\nDetails:\n```\n{error_details}\n```"
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": error_msg})
        return history, ""


def get_workflow_status(user_id: str = "test_user"):
    """Get current workflow status showing session state."""
    try:
        chatbot = get_or_create_chatbot(user_id)

        materials_count = chatbot.get_materials_count()
        conversation_summary = chatbot.get_conversation_summary()

        # Get workflow state information
        state = chatbot.conversation_state
        session_mode = state.get("session_mode", "None")
        tutor_active = state.get("tutor_session_active", False)
        has_analysis = state.get("analysis_results") is not None
        wants_scheduling = state.get("user_wants_scheduling", False)

        status = f"""
### 📊 Enhanced Workflow Status

**User ID:** {user_id}
**Knowledge Base:** {materials_count} document chunks
**{conversation_summary}**

#### Workflow State:
- **Session Mode:** `{session_mode}`
- **Tutor Loop Active:** `{tutor_active}` {"✅" if tutor_active else "❌"}
- **Has Analysis Results:** `{has_analysis}` {"✅" if has_analysis else "❌"}
- **Scheduling Requested:** `{wants_scheduling}` {"✅" if wants_scheduling else "❌"}

#### Workflow Capabilities:
- ✅ Multi-turn tutoring (Tutor → Tutor loops)
- ✅ Auto-analysis (Tutor → Analyzer on exit)
- ✅ Auto-scheduling (Analyzer → Scheduler)
- ✅ Direct routing to all agents
"""
        return status
    except Exception as e:
        return f"❌ Error getting status: {str(e)}"


def clear_conversation(user_id: str = "test_user"):
    """Clear conversation history."""
    try:
        chatbot = get_or_create_chatbot(user_id)
        result = chatbot.clear_conversation()
        return [], f"✅ {result}"
    except Exception as e:
        return [], f"❌ Error: {str(e)}"


def create_test_interface():
    """Create the simplified test interface."""

    with gr.Blocks(title="Study Pal - Enhanced Workflow Test", theme=gr.themes.Soft()) as app:

        gr.Markdown("""
        # 🎓 Study Pal - Enhanced LangGraph Workflow Test

        **Single-Interface Design:** No tabs needed! The enhanced workflow automatically routes your messages:

        | Your Message | Auto-Routes To | Workflow Pattern |
        |--------------|----------------|------------------|
        | Study questions | Tutor Agent | Multi-turn loops (Tutor → Tutor) |
        | "I'm done" | Analyzer Agent | Auto-handoff (Tutor → Analyzer) |
        | "Create schedule" | Scheduler Agent | Pipeline (Analyzer → Scheduler) |
        | "Motivate me" | Motivator Agent | Direct routing |

        **✨ New Features Being Tested:**
        - 🔄 Multi-turn tutoring conversations
        - 🤝 Automatic agent handoffs
        - 🎯 LLM-based exit intent detection
        - 📊 State propagation between agents

        ---
        """)

        # User ID input
        with gr.Row():
            user_id_input = gr.Textbox(
                label="👤 User ID",
                value="test_user",
                placeholder="Enter user ID for testing",
                scale=3
            )
            status_btn = gr.Button("📊 Get Workflow Status", scale=1)

        status_output = gr.Markdown("Ready to test! Upload materials and start chatting.")

        # File upload section
        gr.Markdown("### 📚 Step 1: Upload Study Materials (Optional)")

        with gr.Row():
            file_upload = gr.File(
                label="Upload PDF",
                file_types=[".pdf"],
                type="filepath",
                scale=3
            )
            upload_btn = gr.Button("📤 Upload & Process", variant="primary", scale=1)

        with gr.Row():
            upload_status = gr.Textbox(
                label="Upload Status",
                interactive=False,
                scale=2
            )
            materials_status = gr.Textbox(
                label="Knowledge Base Status",
                value="📚 No materials loaded",
                interactive=False,
                scale=1
            )

        # Main chat interface
        gr.Markdown("### 💬 Step 2: Chat with AI (All Agents Available)")

        chatbot = gr.Chatbot(
            label="Enhanced Multi-Agent Conversation",
            height=500,
            type="messages",
            show_label=True
        )

        with gr.Row():
            msg = gr.Textbox(
                label="Your Message",
                placeholder="Ask anything - the workflow will route automatically...",
                scale=5,
                show_label=False
            )
            submit_btn = gr.Button("📨 Send", variant="primary", scale=1)

        with gr.Row():
            clear_btn = gr.Button("🧹 Clear Conversation")
            clear_status = gr.Textbox(label="Clear Status", interactive=False, show_label=False)

        # Example prompts grouped by workflow pattern
        gr.Markdown("""
        ### 💡 Test the Enhanced Workflow

        **Try these examples to test different workflow patterns:**
        """)

        with gr.Accordion("🔄 Test Multi-Turn Tutoring (Tutor → Tutor Loop)", open=True):
            gr.Examples(
                examples=[
                    "What is machine learning?",
                    "Can you explain neural networks?",
                    "Tell me more about deep learning",
                    "What about backpropagation?",
                ],
                inputs=msg,
                label="Multi-turn conversation examples"
            )

        with gr.Accordion("🎯 Test Exit Detection & Auto-Analysis (Tutor → Analyzer)", open=True):
            gr.Examples(
                examples=[
                    "Thanks, I'm done for now",
                    "I understand now, let's finish",
                    "That's all I needed, analyze my session",
                    "Great explanation! Can you analyze my weak points?",
                ],
                inputs=msg,
                label="Exit intent detection examples"
            )

        with gr.Accordion("📅 Test Full Pipeline (Tutor → Analyzer → Scheduler)", open=True):
            gr.Examples(
                examples=[
                    "I'm done, create a study schedule for tomorrow",
                    "Thanks! Can you analyze and schedule study time from 2-5pm?",
                    "Finish session and make a plan for tomorrow 14:00-17:00",
                ],
                inputs=msg,
                label="Full pipeline examples"
            )

        with gr.Accordion("🎯 Test Direct Routing", open=True):
            gr.Examples(
                examples=[
                    "Schedule study from 14:00 to 17:00 tomorrow",
                    "Analyze my weak points",
                    "I need motivation to study",
                ],
                inputs=msg,
                label="Direct routing examples"
            )

        # Event handlers
        upload_btn.click(
            fn=upload_file,
            inputs=[file_upload, user_id_input],
            outputs=[upload_status, materials_status]
        )

        submit_btn.click(
            fn=chat_with_agents,
            inputs=[msg, chatbot, user_id_input],
            outputs=[chatbot, msg]
        )

        msg.submit(
            fn=chat_with_agents,
            inputs=[msg, chatbot, user_id_input],
            outputs=[chatbot, msg]
        )

        clear_btn.click(
            fn=clear_conversation,
            inputs=[user_id_input],
            outputs=[chatbot, clear_status]
        )

        status_btn.click(
            fn=get_workflow_status,
            inputs=[user_id_input],
            outputs=[status_output]
        )

        # Footer with testing tips
        gr.Markdown("""
        ---
        ### 🧪 Testing Tips

        1. **Test Multi-Turn Loops:** Ask several questions in a row and verify the tutor keeps responding
        2. **Test Exit Detection:** Say "I'm done" and verify it routes to Analyzer automatically
        3. **Test Pipeline:** After tutoring, ask to analyze and schedule - verify all 3 agents run
        4. **Check Workflow Status:** Click "Get Workflow Status" to see internal state changes
        5. **Monitor Logs:** Watch the console for routing decisions and state updates

        **Expected Behavior:**
        - Questions → Tutor responds, `tutor_session_active=True`
        - More questions → Tutor keeps responding (loop)
        - "I'm done" → Analyzer runs, `session_mode=analysis_requested`
        - "Create schedule" after analysis → Scheduler runs with analysis results

        **Files to Check:**
        - `core/workflow_graph.py` - Graph structure
        - `core/workflow_nodes.py` - Routing logic
        - `WORKFLOW_ARCHITECTURE.md` - Complete documentation
        """)

    return app


def main():
    """Launch the test interface."""
    print("\n" + "=" * 80)
    print("  🧪 STUDY PAL - ENHANCED WORKFLOW TEST INTERFACE")
    print("=" * 80)
    print("\n✨ Testing Enhanced Features:")
    print("   • Multi-turn tutoring loops (Tutor → Tutor)")
    print("   • Automatic agent handoffs (Tutor → Analyzer)")
    print("   • Conditional scheduling (Analyzer → Scheduler)")
    print("   • LLM-based exit intent detection")
    print("   • State propagation between agents")
    print("\n📖 See WORKFLOW_ARCHITECTURE.md for complete documentation")
    print("\n" + "=" * 80 + "\n")

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  WARNING: OPENAI_API_KEY not found in environment!")
        print("   Make sure you have a .env file with your API key.\n")

    app = create_test_interface()

    print("\n🌐 Starting test interface...")
    print("   Local:   http://localhost:7860")
    print("   Press Ctrl+C to stop\n")

    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True,
        quiet=False
    )


if __name__ == "__main__":
    main()
