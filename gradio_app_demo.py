"""
Gradio UI for Study Pal - DEMO VERSION with Enhanced Visuals

Enhanced for presentations with:
- Real-time workflow status display
- Visual agent activity indicators
- Colored badges for agent states
- Session analytics dashboard
- Chunk count visualization

All powered by LangGraph multi-agent system!
"""

import os
import logging
from pathlib import Path
import gradio as gr
from dotenv import load_dotenv

from core.langgraph_chatbot import LangGraphChatbot
from agents.user_profile import UserProfileStore, UserProfile
from agents.motivator_agent import MotivatorAgent, OpenAIMotivationModel
from agents.quote_scraper import WebSearchQuoteScraper

# Load environment variables
load_dotenv()

# Configure logging
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gradio_app_demo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global chatbot instance (will be initialized per session)
chatbot_instances = {}

def get_or_create_chatbot(user_id: str = "demo_user") -> LangGraphChatbot:
    """Get or create a chatbot instance for a user."""
    if user_id not in chatbot_instances:
        chatbot_instances[user_id] = LangGraphChatbot(user_id=user_id, session_id=user_id)
    return chatbot_instances[user_id]


def get_workflow_status_html(user_id: str = "demo_user"):
    """Get current workflow status with visual indicators."""
    try:
        chatbot = get_or_create_chatbot(user_id)
        state = chatbot.conversation_state

        # Get state values
        current_intent = state.get("current_intent", "unknown")
        tutor_active = state.get("tutor_session_active", False)
        has_analysis = state.get("analysis_results") is not None
        awaiting_schedule = state.get("awaiting_schedule_confirmation", False)
        session_mode = state.get("session_mode", "idle")

        # Agent colors and emojis
        agent_info = {
            "tutor": ("🎓", "#3B82F6", "Tutor"),
            "scheduler": ("📅", "#F59E0B", "Scheduler"),
            "analyzer": ("🔍", "#10B981", "Analyzer"),
            "motivator": ("💪", "#8B5CF6", "Motivator"),
            "unknown": ("🤖", "#6B7280", "Router")
        }

        emoji, color, name = agent_info.get(current_intent, agent_info["unknown"])

        # Build status HTML
        html = f"""
        <div style="padding: 15px; background: linear-gradient(135deg, {color}22 0%, {color}11 100%);
                    border-radius: 10px; border-left: 4px solid {color};">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                <span style="font-size: 32px;">{emoji}</span>
                <div>
                    <div style="font-size: 18px; font-weight: bold; color: {color};">
                        Current Agent: {name}
                    </div>
                    <div style="font-size: 12px; color: #6B7280; text-transform: uppercase; letter-spacing: 1px;">
                        Mode: {session_mode.replace('_', ' ')}
                    </div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 15px;">
                <div style="background: white; padding: 10px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 20px;">{"✅" if tutor_active else "⏸️"}</div>
                    <div style="font-size: 11px; color: #6B7280; margin-top: 4px;">Tutoring</div>
                </div>
                <div style="background: white; padding: 10px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 20px;">{"✅" if has_analysis else "⏸️"}</div>
                    <div style="font-size: 11px; color: #6B7280; margin-top: 4px;">Analyzed</div>
                </div>
                <div style="background: white; padding: 10px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 20px;">{"⏳" if awaiting_schedule else "⏸️"}</div>
                    <div style="font-size: 11px; color: #6B7280; margin-top: 4px;">Scheduling</div>
                </div>
            </div>
        </div>
        """

        return html
    except Exception as e:
        return f'<div style="color: red;">Error: {str(e)}</div>'


def get_knowledge_base_html(user_id: str = "demo_user"):
    """Get knowledge base status with visual chunk indicator."""
    try:
        chatbot = get_or_create_chatbot(user_id)
        count = chatbot.get_materials_count()

        # Calculate visual indicator (progress bar)
        max_chunks = 500  # Arbitrary max for visual purposes
        percentage = min((count / max_chunks) * 100, 100)

        # Color based on chunk count
        if count == 0:
            color = "#6B7280"
            status = "No materials"
        elif count < 50:
            color = "#F59E0B"
            status = "Getting started"
        elif count < 200:
            color = "#3B82F6"
            status = "Building knowledge"
        else:
            color = "#10B981"
            status = "Rich knowledge base"

        html = f"""
        <div style="padding: 15px; background: white; border-radius: 10px;
                    border: 2px solid {color}; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div>
                    <div style="font-size: 14px; font-weight: bold; color: #1F2937;">
                        📚 Knowledge Base
                    </div>
                    <div style="font-size: 12px; color: #6B7280;">
                        {status}
                    </div>
                </div>
                <div style="font-size: 28px; font-weight: bold; color: {color};">
                    {count}
                </div>
            </div>

            <div style="background: #E5E7EB; height: 8px; border-radius: 4px; overflow: hidden;">
                <div style="background: {color}; height: 100%; width: {percentage}%;
                            transition: width 0.5s ease;"></div>
            </div>

            <div style="font-size: 10px; color: #9CA3AF; text-align: right; margin-top: 4px;">
                {count} / {max_chunks} chunks
            </div>
        </div>
        """

        return html
    except Exception as e:
        return f'<div style="color: red;">Error: {str(e)}</div>'


def get_session_analytics_html(user_id: str = "demo_user"):
    """Get session analytics dashboard."""
    try:
        chatbot = get_or_create_chatbot(user_id)
        state = chatbot.conversation_state

        # Count message types
        messages = state.get("messages", [])
        user_msgs = sum(1 for msg in messages if hasattr(msg, 'type') and msg.type == "human")
        ai_msgs = sum(1 for msg in messages if hasattr(msg, 'type') and msg.type == "ai")

        # Get weak points
        analysis = state.get("analysis_results")
        weak_points_count = len(analysis.weak_points) if analysis and hasattr(analysis, 'weak_points') else 0

        # Get schedule info
        has_schedule = state.get("generated_schedule") is not None

        html = f"""
        <div style="padding: 15px; background: linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%);
                    border-radius: 10px;">
            <div style="font-size: 16px; font-weight: bold; color: #1F2937; margin-bottom: 15px;">
                📊 Session Analytics
            </div>

            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
                <div style="background: white; padding: 12px; border-radius: 8px; border-left: 3px solid #3B82F6;">
                    <div style="font-size: 24px; font-weight: bold; color: #3B82F6;">{user_msgs}</div>
                    <div style="font-size: 12px; color: #6B7280;">Questions Asked</div>
                </div>

                <div style="background: white; padding: 12px; border-radius: 8px; border-left: 3px solid #10B981;">
                    <div style="font-size: 24px; font-weight: bold; color: #10B981;">{ai_msgs}</div>
                    <div style="font-size: 12px; color: #6B7280;">AI Responses</div>
                </div>

                <div style="background: white; padding: 12px; border-radius: 8px; border-left: 3px solid #EF4444;">
                    <div style="font-size: 24px; font-weight: bold; color: #EF4444;">{weak_points_count}</div>
                    <div style="font-size: 12px; color: #6B7280;">Weak Points</div>
                </div>

                <div style="background: white; padding: 12px; border-radius: 8px; border-left: 3px solid #F59E0B;">
                    <div style="font-size: 24px; font-weight: bold; color: #F59E0B;">{"✅" if has_schedule else "⏸️"}</div>
                    <div style="font-size: 12px; color: #6B7280;">Schedule Created</div>
                </div>
            </div>
        </div>
        """

        return html
    except Exception as e:
        return f'<div style="color: red;">Error: {str(e)}</div>'


def upload_file(file, user_id: str = "demo_user"):
    """Handle file upload with enhanced feedback."""
    if file is None:
        return "Please upload a file first.", get_knowledge_base_html(user_id)

    try:
        chatbot = get_or_create_chatbot(user_id)
        file_path = Path(file)

        # Ingest the material
        result = chatbot.ingest_material(file_path)
        count = chatbot.get_materials_count()

        return (
            f"✅ {result}\n\n📊 Total chunks in knowledge base: **{count}**",
            get_knowledge_base_html(user_id)
        )
    except Exception as e:
        return f"❌ Error: {str(e)}", get_knowledge_base_html(user_id)


def chat_with_tutor(message, history, user_id: str = "demo_user"):
    """Handle chat with live workflow status updates."""
    if not message.strip():
        return history, "", get_workflow_status_html(user_id), get_session_analytics_html(user_id)

    try:
        from core.agent_avatars import get_user_avatar

        chatbot = get_or_create_chatbot(user_id)

        # Get response from LangGraph workflow
        response = chatbot.chat(message)

        # Get the current agent's avatar
        agent_avatar = chatbot.get_current_avatar()
        user_avatar = get_user_avatar()

        # Update history with avatars in metadata
        history.append({"role": "user", "content": message, "metadata": {"avatar": user_avatar}})
        history.append({"role": "assistant", "content": response, "metadata": {"avatar": agent_avatar}})

        return (
            history,
            "",
            get_workflow_status_html(user_id),
            get_session_analytics_html(user_id)
        )
    except Exception as e:
        from core.agent_avatars import get_user_avatar, get_agent_avatar

        error_msg = f"❌ Error: {str(e)}"
        user_avatar = get_user_avatar()
        system_avatar = get_agent_avatar("system")

        history.append({"role": "user", "content": message, "metadata": {"avatar": user_avatar}})
        history.append({"role": "assistant", "content": error_msg, "metadata": {"avatar": system_avatar}})
        return (
            history,
            "",
            get_workflow_status_html(user_id),
            get_session_analytics_html(user_id)
        )


def clear_conversation(user_id: str = "demo_user"):
    """Clear conversation and reset displays."""
    try:
        chatbot = get_or_create_chatbot(user_id)
        result = chatbot.clear_conversation()
        return (
            [],
            f"✅ {result}",
            get_workflow_status_html(user_id),
            get_session_analytics_html(user_id)
        )
    except Exception as e:
        return [], f"❌ Error: {str(e)}", "", ""


def handle_login(username: str):
    """Handle user login - returns tuple matching outputs order."""
    if not username or not username.strip():
        return (
            "❌ Please enter a username",  # login_status
            gr.update(visible=True),  # login_container
            gr.update(visible=False),  # main_container
            None,  # user_id_state
            False,  # logged_in_state
            "### 🎓 Study Pal",  # current_user_display
            get_workflow_status_html(),  # workflow_status
            get_knowledge_base_html(),  # knowledge_base_status
            get_session_analytics_html()  # session_analytics
        )

    try:
        # Check if user profile exists
        profiles_dir = Path("data/profiles")
        profiles_dir.mkdir(parents=True, exist_ok=True)
        profile_store = UserProfileStore(root=profiles_dir)

        try:
            profile = profile_store.load(username)
            # User exists, login successful
            return (
                "",  # login_status (clear it)
                gr.update(visible=False),  # login_container
                gr.update(visible=True),  # main_container
                username,  # user_id_state
                True,  # logged_in_state
                f"### 🎓 Study Pal - Logged in as: **{profile.name}** (@{username})",  # current_user_display
                get_workflow_status_html(username),  # workflow_status
                get_knowledge_base_html(username),  # knowledge_base_status
                get_session_analytics_html(username)  # session_analytics
            )
        except:
            return (
                f"❌ User '{username}' not found. Please create an account first.",  # login_status
                gr.update(visible=True),  # login_container
                gr.update(visible=False),  # main_container
                None,  # user_id_state
                False,  # logged_in_state
                "### 🎓 Study Pal",  # current_user_display
                get_workflow_status_html(),  # workflow_status
                get_knowledge_base_html(),  # knowledge_base_status
                get_session_analytics_html()  # session_analytics
            )
    except Exception as e:
        return (
            f"❌ Error: {str(e)}",  # login_status
            gr.update(visible=True),  # login_container
            gr.update(visible=False),  # main_container
            None,  # user_id_state
            False,  # logged_in_state
            "### 🎓 Study Pal",  # current_user_display
            get_workflow_status_html(),  # workflow_status
            get_knowledge_base_html(),  # knowledge_base_status
            get_session_analytics_html()  # session_analytics
        )


def handle_signup(username: str, name: str, field: str, persona: str, weakness: str, goals: str):
    """Handle new user signup - returns tuple matching outputs order."""
    if not username or not username.strip():
        return (
            "❌ Please enter a username",  # signup_status
            gr.update(visible=True),  # login_container
            gr.update(visible=False),  # main_container
            None,  # user_id_state
            False,  # logged_in_state
            "### 🎓 Study Pal",  # current_user_display
            get_workflow_status_html(),  # workflow_status
            get_knowledge_base_html(),  # knowledge_base_status
            get_session_analytics_html()  # session_analytics
        )

    if not name or not name.strip():
        return (
            "❌ Please enter your name",  # signup_status
            gr.update(visible=True),  # login_container
            gr.update(visible=False),  # main_container
            None,  # user_id_state
            False,  # logged_in_state
            "### 🎓 Study Pal",  # current_user_display
            get_workflow_status_html(),  # workflow_status
            get_knowledge_base_html(),  # knowledge_base_status
            get_session_analytics_html()  # session_analytics
        )

    try:
        # Create user profile
        profiles_dir = Path("data/profiles")
        profiles_dir.mkdir(parents=True, exist_ok=True)
        profile_store = UserProfileStore(root=profiles_dir)

        # Check if username already exists
        try:
            existing = profile_store.load(username)
            return (
                f"❌ Username '{username}' already exists. Please login instead.",  # signup_status
                gr.update(visible=True),  # login_container
                gr.update(visible=False),  # main_container
                None,  # user_id_state
                False,  # logged_in_state
                "### 🎓 Study Pal",  # current_user_display
                get_workflow_status_html(),  # workflow_status
                get_knowledge_base_html(),  # knowledge_base_status
                get_session_analytics_html()  # session_analytics
            )
        except:
            pass  # User doesn't exist, continue with signup

        # Create new profile
        profile = UserProfile(
            user_id=username,
            name=name,
            primary_persona=persona if persona and persona.strip() else "motivational coach",
            academic_field=field
        )

        # Add goals if provided
        if goals and goals.strip():
            profile.goals = [goals.strip()]

        # Add weakness traits if provided
        if weakness and weakness.strip():
            # Split by comma if multiple weaknesses are provided
            weakness_list = [w.strip() for w in weakness.split(",") if w.strip()]
            profile.traits = weakness_list

        profile_store.save(profile)

        # Signup successful
        return (
            "",  # signup_status (clear it)
            gr.update(visible=False),  # login_container
            gr.update(visible=True),  # main_container
            username,  # user_id_state
            True,  # logged_in_state
            f"### 🎓 Study Pal - Logged in as: **{name}** (@{username})",  # current_user_display
            get_workflow_status_html(username),  # workflow_status
            get_knowledge_base_html(username),  # knowledge_base_status
            get_session_analytics_html(username)  # session_analytics
        )
    except Exception as e:
        return (
            f"❌ Error: {str(e)}",  # signup_status
            gr.update(visible=True),  # login_container
            gr.update(visible=False),  # main_container
            None,  # user_id_state
            False,  # logged_in_state
            "### 🎓 Study Pal",  # current_user_display
            get_workflow_status_html(),  # workflow_status
            get_knowledge_base_html(),  # knowledge_base_status
            get_session_analytics_html()  # session_analytics
        )


def handle_logout():
    """Handle user logout - returns tuple matching outputs order."""
    return (
        gr.update(visible=True),  # login_container
        gr.update(visible=False),  # main_container
        None,  # user_id_state
        False,  # logged_in_state
        [],  # chatbot
        "",  # login_status
        "",  # signup_status
        "",  # login_username
        "",  # signup_username
        "",  # signup_name
        ""  # signup_goals
    )


def quick_reset_demo(user_id: str):
    """Quick reset for demo purposes - clears conversation but keeps user logged in."""
    if not user_id:
        return [], "⚠️ Please login first", get_workflow_status_html(), get_session_analytics_html()

    try:
        chatbot = get_or_create_chatbot(user_id)
        result = chatbot.clear_conversation()
        return (
            [],
            f"✅ Demo reset! Ready for next demo run.",
            get_workflow_status_html(user_id),
            get_session_analytics_html(user_id)
        )
    except Exception as e:
        return [], f"❌ Error: {str(e)}", "", ""


def create_demo_interface():
    """Create the DEMO Gradio interface with enhanced visuals and login system."""

    with gr.Blocks(
        title="Study Pal - AI Study Assistant DEMO",
        theme=gr.themes.Soft(primary_hue="blue", secondary_hue="purple"),
        css="""
        .large-text textarea { font-size: 18px !important; }
        .large-text { font-size: 18px !important; }
        .demo-badge { background: #8B5CF6; color: white; padding: 8px 16px;
                      border-radius: 20px; display: inline-block; font-weight: bold; }
        .progress-step { padding: 12px; border-radius: 8px; text-align: center;
                        font-size: 14px; font-weight: 600; transition: all 0.3s; }
        .step-active { background: #3B82F6; color: white; }
        .step-completed { background: #10B981; color: white; }
        .step-pending { background: #E5E7EB; color: #6B7280; }
        """
    ) as app:

        # State
        user_id_state = gr.State(None)
        logged_in_state = gr.State(False)

        # Login/Main App visibility states
        login_screen = gr.State(True)
        main_app_screen = gr.State(False)

        # ========== LOGIN/SIGNUP SCREEN ==========
        with gr.Column(visible=True) as login_container:
            gr.Markdown("""
            # 🎓 Study Pal
            ## Multi-Agent AI Study Assistant Demo

            <div class="demo-badge">🎬 PRESENTATION MODE</div>

            ### Powered by LangGraph Multi-Agent Orchestration
            """)

            gr.Markdown("---")

            with gr.Tabs() as login_tabs:
                # Login Tab
                with gr.Tab("🔑 Login"):
                    gr.Markdown("### Welcome Back!")
                    login_username = gr.Textbox(
                        label="Username",
                        placeholder="Enter your username",
                        elem_classes=["large-text"]
                    )
                    login_btn = gr.Button("Login", variant="primary", size="lg")
                    login_status = gr.Markdown("")

                # Signup Tab
                with gr.Tab("✨ Create Account"):
                    gr.Markdown("### Create Your Profile")

                    signup_username = gr.Textbox(
                        label="Username",
                        placeholder="Choose a username (e.g., john_doe)",
                        elem_classes=["large-text"]
                    )
                    signup_name = gr.Textbox(
                        label="Your Name",
                        placeholder="Enter your full name",
                        elem_classes=["large-text"]
                    )
                    signup_field = gr.Dropdown(
                        label="Academic Field",
                        choices=[
                            "AI & Machine Learning",
                            "Computer Science",
                            "Mathematics",
                            "Physics",
                            "Biology",
                            "Chemistry",
                            "Engineering",
                            "Business",
                            "Other"
                        ],
                        value="AI & Machine Learning"
                    )
                    signup_persona = gr.Textbox(
                        label="Preferred Motivational Persona",
                        placeholder="e.g., Steve Jobs, Albert Einstein, Motivational Coach, etc.",
                        elem_classes=["large-text"]
                    )
                    signup_weakness = gr.Textbox(
                        label="Weakness Traits",
                        placeholder="What are your main challenges or weaknesses? (e.g., procrastination, difficulty with math)",
                        lines=2,
                        elem_classes=["large-text"]
                    )
                    signup_goals = gr.Textbox(
                        label="Learning Goals",
                        placeholder="What do you want to achieve? (e.g., Master deep learning concepts)",
                        lines=3,
                        elem_classes=["large-text"]
                    )

                    signup_btn = gr.Button("Create Account & Start", variant="primary", size="lg")
                    signup_status = gr.Markdown("")

            gr.Markdown("---")
            gr.Markdown("""
            <div style="text-align: center; color: #6B7280; font-size: 14px;">
            <b>Demo Features:</b>
            Multi-agent orchestration • RAG-powered tutoring • Session analysis •
            Pomodoro scheduling • Persona-based motivation
            </div>
            """)

        # ========== MAIN APP SCREEN ==========
        with gr.Column(visible=False) as main_container:
            # Header with logout
            with gr.Row():
                with gr.Column(scale=4):
                    current_user_display = gr.Markdown("### 🎓 Study Pal - Logged in as: **User**")
                with gr.Column(scale=1):
                    logout_btn = gr.Button("🚪 Logout", variant="secondary")

            gr.Markdown("""
            <div style="text-align: center; margin: 10px 0;">
            <span class="demo-badge">🎬 DEMO MODE - LangGraph Multi-Agent System</span>
            </div>
            """)

            # Workflow Progress Timeline
            workflow_progress = gr.HTML("""
            <div style="padding: 20px; background: linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%);
                        border-radius: 12px; margin-bottom: 20px;">
                <div style="font-size: 14px; font-weight: bold; color: #1F2937; margin-bottom: 12px; text-align: center;">
                    📊 WORKFLOW PROGRESS
                </div>
                <div style="display: flex; justify-content: space-between; gap: 8px;">
                    <div class="progress-step step-pending">
                        📚<br>Upload
                    </div>
                    <div class="progress-step step-pending">
                        🎓<br>Tutor
                    </div>
                    <div class="progress-step step-pending">
                        🔍<br>Analyze
                    </div>
                    <div class="progress-step step-pending">
                        📅<br>Schedule
                    </div>
                    <div class="progress-step step-pending">
                        💪<br>Motivate
                    </div>
                </div>
            </div>
            """)

            # Top status row
            with gr.Row():
                workflow_status = gr.HTML(
                    value=get_workflow_status_html(),
                    label="Workflow Status"
                )
                knowledge_base_status = gr.HTML(
                    value=get_knowledge_base_html(),
                    label="Knowledge Base"
                )

            # Main tabs
            with gr.Tabs() as tabs:
                # Tab 1: Upload & Chat (Combined for demo flow)
                with gr.Tab("💬 Interactive Session"):
                    with gr.Row():
                        with gr.Column(scale=2):
                            gr.Markdown("### Chat with AI Agents")
                            gr.Markdown("""
                            The system automatically routes to the right agent:
                            - 🎓 **Tutor** - Study questions (RAG-powered)
                            - 🔍 **Analyzer** - Session analysis
                            - 📅 **Scheduler** - Study planning
                            - 💪 **Motivator** - Encouragement
                            """)

                            chatbot = gr.Chatbot(
                                label="Study Pal Conversation",
                                height=450,
                                type="messages",
                                avatar_images=("👤", "🤖"),
                                elem_classes=["large-text"]
                            )

                            with gr.Row():
                                msg = gr.Textbox(
                                    label="Your Message",
                                    placeholder="Ask a question, request analysis, or schedule a session...",
                                    scale=5,
                                    elem_classes=["large-text"]
                                )
                                submit_btn = gr.Button("Send", variant="primary", scale=1)

                            with gr.Row():
                                clear_btn = gr.Button("🧹 Clear Conversation", variant="secondary", scale=1)
                                reset_demo_btn = gr.Button("🔄 Quick Reset", variant="stop", scale=1)

                            clear_status = gr.Textbox(label="Status", interactive=False, elem_classes=["large-text"])

                            # Example prompts
                            gr.Examples(
                                examples=[
                                    "What is machine learning?",
                                    "I'm done, analyze my session",
                                    "Yes, schedule another session",
                                    "Tomorrow 2-5pm",
                                    "Give me motivation"
                                ],
                                inputs=msg,
                                label="🎯 Demo Flow Examples"
                            )

                        with gr.Column(scale=1):
                            gr.Markdown("### 📊 Live Analytics")

                            session_analytics = gr.HTML(
                                value=get_session_analytics_html(),
                                label="Session Analytics"
                            )

                            gr.Markdown("---")
                            gr.Markdown("### 📚 Upload Materials")

                            file_upload = gr.File(
                                label="Upload PDF",
                                file_types=[".pdf"],
                                type="filepath"
                            )
                            upload_btn = gr.Button("Upload & Process", variant="primary")
                            upload_status = gr.Markdown("No files uploaded yet.")

                # Tab 2: Motivation
                with gr.Tab("💪 Motivation"):
                    gr.Markdown("""
                    ### Get Personalized Motivation

                    Receive inspiring messages tailored to your profile!
                    """)

                    motivation_btn = gr.Button("✨ Get Motivation", variant="primary", size="lg")
                    motivation_output = gr.Markdown("Click the button to get motivated!")

        # Event handlers
        submit_btn.click(
            fn=chat_with_tutor,
            inputs=[msg, chatbot, user_id_state],
            outputs=[chatbot, msg, workflow_status, session_analytics]
        )

        msg.submit(
            fn=chat_with_tutor,
            inputs=[msg, chatbot, user_id_state],
            outputs=[chatbot, msg, workflow_status, session_analytics]
        )

        clear_btn.click(
            fn=clear_conversation,
            inputs=[user_id_state],
            outputs=[chatbot, clear_status, workflow_status, session_analytics]
        )

        upload_btn.click(
            fn=upload_file,
            inputs=[file_upload, user_id_state],
            outputs=[upload_status, knowledge_base_status]
        )

        def get_motivation_demo(user_id):
            """Get motivation with fallback for demo."""
            try:
                profiles_dir = Path("data/profiles")
                profiles_dir.mkdir(parents=True, exist_ok=True)
                profile_store = UserProfileStore(root=profiles_dir)

                try:
                    profile = profile_store.load(user_id)
                    persona = profile.primary_persona or "motivational coach"
                except:
                    # Create demo profile if doesn't exist
                    profile = UserProfile(
                        user_id=user_id,
                        name="Demo User",
                        primary_persona="Steve Jobs",
                        academic_field="AI & Machine Learning"
                    )
                    profile_store.save(profile)
                    persona = "Steve Jobs"

                motivator = MotivatorAgent(
                    profile_store=profile_store,
                    llm=OpenAIMotivationModel()
                )

                scraper = WebSearchQuoteScraper()
                motivation_msg = motivator.craft_personalized_message(
                    user_id=user_id,
                    scraper=scraper
                )

                return f"### 💪 Motivation from {persona.title()}\n\n{motivation_msg.text}"
            except Exception as e:
                return f"❌ Error: {str(e)}"

        motivation_btn.click(
            fn=get_motivation_demo,
            inputs=[user_id_state],
            outputs=[motivation_output]
        )

        # Login/Signup handlers
        login_btn.click(
            fn=handle_login,
            inputs=[login_username],
            outputs=[
                login_status,
                login_container,
                main_container,
                user_id_state,
                logged_in_state,
                current_user_display,
                workflow_status,
                knowledge_base_status,
                session_analytics
            ]
        )

        signup_btn.click(
            fn=handle_signup,
            inputs=[signup_username, signup_name, signup_field, signup_persona, signup_weakness, signup_goals],
            outputs=[
                signup_status,
                login_container,
                main_container,
                user_id_state,
                logged_in_state,
                current_user_display,
                workflow_status,
                knowledge_base_status,
                session_analytics
            ]
        )

        logout_btn.click(
            fn=handle_logout,
            outputs=[
                login_container,
                main_container,
                user_id_state,
                logged_in_state,
                chatbot,
                login_status,
                signup_status,
                login_username,
                signup_username,
                signup_name,
                signup_goals
            ]
        )

        reset_demo_btn.click(
            fn=quick_reset_demo,
            inputs=[user_id_state],
            outputs=[chatbot, clear_status, workflow_status, session_analytics]
        )

    return app


def main():
    """Launch the DEMO Gradio app."""
    print("\n" + "=" * 70)
    print("  🎓 STUDY PAL - DEMO UI (Enhanced for Presentations)")
    print("=" * 70)
    print("\n✨ Features:")
    print("  • Real-time workflow status visualization")
    print("  • Live session analytics dashboard")
    print("  • Visual agent activity indicators")
    print("  • Enhanced knowledge base display")
    print("\n🚀 Starting Gradio interface...\n")

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  WARNING: OPENAI_API_KEY not found!")
        print("   Make sure you have a .env file with your API key.\n")

    app = create_demo_interface()

    print("\n🌐 Access the demo at:")
    print("   http://localhost:7860")
    print("\n   Press Ctrl+C to stop\n")

    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True,
        quiet=False
    )


if __name__ == "__main__":
    main()
