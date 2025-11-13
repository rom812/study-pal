"""
Gradio UI for Study Pal - Interactive Multi-Agent Study Assistant

This provides a user-friendly web interface for:
- Uploading study materials (PDFs)
- Chatting with AI tutor
- Analyzing study sessions
- Creating study schedules
- Getting personalized motivation

All powered by LangGraph multi-agent system!
"""

import os
from pathlib import Path
import gradio as gr
from dotenv import load_dotenv

from core.langgraph_chatbot import LangGraphChatbot
from agents.onboarding import OnboardingAgent
from agents.motivator_agent import MotivatorAgent
from core.weakness_analyzer import SessionRecommendations

# Load environment variables
load_dotenv()

# Global chatbot instance (will be initialized per session)
chatbot_instances = {}
user_profiles = {}  # Store user profiles
logged_in_user = {}  # Track logged-in user per session


def get_or_create_chatbot(user_id: str = "default_user") -> LangGraphChatbot:
    """Get or create a chatbot instance for a user."""
    if user_id not in chatbot_instances:
        chatbot_instances[user_id] = LangGraphChatbot(user_id=user_id, session_id=user_id)
    return chatbot_instances[user_id]


def check_user_profile(user_id: str):
    """Check if user has completed onboarding."""
    from pathlib import Path
    profile_path = Path(f"data/profiles/{user_id}.json")
    return profile_path.exists()


def validate_user_exists(user_id: str) -> tuple[bool, str]:
    """Validate if a user exists in the system."""
    if not user_id or not user_id.strip():
        return False, "Please enter a user ID."

    user_id = user_id.strip()
    profile_path = Path(f"data/profiles/{user_id}.json")

    if profile_path.exists():
        return True, f"Welcome back, {user_id}!"
    else:
        return False, f"User ID '{user_id}' not found. Please check your ID or create a new profile."


def login_user(user_id: str, session_state: dict) -> tuple[bool, str, dict]:
    """
    Login user and update session state.
    Returns: (success, message, updated_session_state)
    """
    is_valid, message = validate_user_exists(user_id)

    if is_valid:
        user_id = user_id.strip()
        session_state["logged_in"] = True
        session_state["user_id"] = user_id
        return True, message, session_state
    else:
        session_state["logged_in"] = False
        session_state["user_id"] = None
        return False, message, session_state


def logout_user(session_state: dict) -> dict:
    """Logout user and clear session state."""
    session_state["logged_in"] = False
    session_state["user_id"] = None
    return session_state


def handle_login(user_id: str, session_state: dict):
    """
    Handle login button click - only for existing users.
    Returns: (session_state, message, login_visible, main_visible, user_display)
    """
    success, message, session_state = login_user(user_id, session_state)

    if success:
        # Hide login, show main app
        return (
            session_state,
            f"✅ {message}",
            gr.update(visible=False),  # login_screen
            gr.update(visible=True),   # main_app
            user_id  # logged_user_display
        )
    else:
        # Keep login visible, hide main app
        return (
            session_state,
            f"❌ {message}",
            gr.update(visible=True),   # login_screen
            gr.update(visible=False),  # main_app
            ""  # logged_user_display
        )


def handle_create_account(user_id: str, name: str, persona: str, focus_area: str, session_state: dict):
    """
    Handle account creation - creates profile and logs user in.
    Returns: (session_state, message, login_visible, main_visible, user_display)
    """
    # Validate inputs
    if not user_id or not user_id.strip():
        return (
            session_state,
            "❌ Please enter a user ID.",
            gr.update(visible=True),
            gr.update(visible=False),
            ""
        )

    if not name or not name.strip():
        return (
            session_state,
            "❌ Please enter your name.",
            gr.update(visible=True),
            gr.update(visible=False),
            ""
        )

    if not focus_area or not focus_area.strip():
        return (
            session_state,
            "❌ Please enter your academic focus.",
            gr.update(visible=True),
            gr.update(visible=False),
            ""
        )

    user_id = user_id.strip()

    # Check if user already exists
    profile_path = Path(f"data/profiles/{user_id}.json")
    if profile_path.exists():
        return (
            session_state,
            f"❌ User ID '{user_id}' already exists. Please login or choose a different ID.",
            gr.update(visible=True),
            gr.update(visible=False),
            ""
        )

    # Create the profile
    try:
        from agents.user_profile import UserProfile, UserProfileStore

        profiles_dir = Path("data/profiles")
        profiles_dir.mkdir(parents=True, exist_ok=True)
        profile_store = UserProfileStore(root=profiles_dir)

        profile = UserProfile(
            user_id=user_id,
            name=name.strip(),
            primary_persona=persona.strip() if persona else "motivational coach",
            preferred_personas=[persona.strip()] if persona else ["motivational coach"],
            academic_field=focus_area.strip(),
            study_topics=[],
            goals=[],
            traits=[],
            current_focus=None
        )

        profile_store.save(profile)

        # Log the user in
        session_state["logged_in"] = True
        session_state["user_id"] = user_id

        return (
            session_state,
            f"✅ Account created successfully! Welcome, {name}!",
            gr.update(visible=False),  # login_screen
            gr.update(visible=True),   # main_app
            user_id  # logged_user_display
        )

    except Exception as e:
        return (
            session_state,
            f"❌ Error creating account: {str(e)}",
            gr.update(visible=True),
            gr.update(visible=False),
            ""
        )


def handle_logout(session_state: dict):
    """
    Handle logout button click.
    Returns: (session_state, login_status, login_visible, main_visible, user_display, login_user_id)
    """
    session_state = logout_user(session_state)

    return (
        session_state,
        "",  # Clear login status
        gr.update(visible=True),   # login_screen
        gr.update(visible=False),  # main_app
        "",  # Clear logged_user_display
        ""   # Clear login_user_id textbox
    )


def create_user_profile(user_id: str, name: str, persona: str, focus_area: str, learning_goals: str, pain_points: str):
    """Create a new user profile through onboarding."""
    try:
        from agents.user_profile import UserProfile, UserProfileStore

        # Validate required fields
        if not name or not name.strip():
            return "❌ Error: Name is required!"
        if not focus_area or not focus_area.strip():
            return "❌ Error: Academic Focus is required!"

        # Initialize profile store with the profiles directory
        profiles_dir = Path("data/profiles")
        profiles_dir.mkdir(parents=True, exist_ok=True)
        profile_store = UserProfileStore(root=profiles_dir)

        # Parse comma-separated lists
        goals_list = [g.strip() for g in learning_goals.split(",")] if learning_goals else []
        pain_points_list = [p.strip() for p in pain_points.split(",")] if pain_points else []

        # Create profile directly
        profile = UserProfile(
            user_id=user_id,
            name=name.strip(),
            primary_persona=persona,
            preferred_personas=[persona],  # Can expand this later
            academic_field=focus_area.strip(),
            study_topics=[],  # Will be populated from uploaded materials
            goals=goals_list,
            traits=pain_points_list,
            current_focus=None
        )

        # Save profile
        profile_store.save(profile)
        user_profiles[user_id] = profile

        return f"""
### ✅ Profile Created Successfully!

**Name:** {name}
**Persona:** {persona}
**Focus Area:** {focus_area}
**Learning Goals:** {len(goals_list)} goals set
**Pain Points:** {len(pain_points_list)} identified

You're all set! Now you can:
1. Upload study materials in the "📚 Upload Materials" tab
2. Start chatting with your AI tutor in the "💬 Chat" tab
3. Get personalized motivation from {persona} in the "💪 Get Motivated" tab
"""
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return f"❌ Error creating profile: {str(e)}\n\nDetails:\n```\n{error_details}\n```"


def upload_file(file, user_id: str = "default_user"):
    """Handle file upload and ingestion."""
    if file is None:
        return "Please upload a file first.", 0, "No materials loaded."

    try:
        chatbot = get_or_create_chatbot(user_id)

        # Get the file path from the upload (filepath type returns string directly)
        file_path = Path(file)

        # Ingest the material
        result = chatbot.ingest_material(file_path)

        # Get updated count
        count = chatbot.get_materials_count()

        return (
            f"✅ {result}",
            count,
            f"📚 Knowledge base: {count} chunks"
        )
    except Exception as e:
        return f"❌ Error: {str(e)}", 0, "Error loading materials"


def chat_with_tutor(message, history, user_id: str = "default_user"):
    """Handle chat messages with the multi-agent system."""
    if not message.strip():
        return history, ""

    try:
        chatbot = get_or_create_chatbot(user_id)

        # Get response from LangGraph workflow (auto-routes to correct agent)
        response = chatbot.chat(message)

        # Update history (using new message format)
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": response})

        return history, ""
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": error_msg})
        return history, ""


def get_system_status(user_id: str = "default_user"):
    """Get current system status."""
    try:
        chatbot = get_or_create_chatbot(user_id)

        materials_count = chatbot.get_materials_count()
        conversation_summary = chatbot.get_conversation_summary()
        last_intent = chatbot.get_last_intent()

        status = f"""
### 📊 System Status

**User ID:** {user_id}
**Mode:** LangGraph Multi-Agent System
**Knowledge Base:** {materials_count} document chunks
**{conversation_summary}**
"""

        if last_intent and last_intent != "unknown":
            status += f"**Last Intent:** {last_intent}  \n"

        return status
    except Exception as e:
        return f"❌ Error getting status: {str(e)}"


def analyze_study_session(session_topic: str = "", user_id: str = "default_user"):
    """Analyze the study session and show weak points."""
    try:
        chatbot = get_or_create_chatbot(user_id)

        # Check if there's enough conversation
        if len(chatbot.conversation_state.get("messages", [])) < 2:
            return "⚠️ Not enough conversation to analyze. Have a study session first!"

        # Analyze session
        topic = session_topic.strip() if session_topic.strip() else None
        recommendations = chatbot.analyze_session(session_topic=topic)

        # Format the analysis
        return format_session_analysis(recommendations)
    except Exception as e:
        return f"❌ Error analyzing session: {str(e)}"


def format_session_analysis(recommendations: SessionRecommendations) -> str:
    """Format session analysis for display."""
    output = f"""
## 📊 Session Analysis Report

### 📝 Summary
{recommendations.session_summary}

"""

    # Weak points
    if recommendations.weak_points:
        output += f"### 🎯 Areas for Improvement ({len(recommendations.weak_points)} identified)\n\n"

        for idx, wp in enumerate(recommendations.weak_points, 1):
            # Difficulty indicator
            if wp.difficulty_level == "severe":
                icon = "🔴"
            elif wp.difficulty_level == "moderate":
                icon = "🟡"
            else:
                icon = "🟢"

            output += f"{idx}. {icon} **{wp.topic.upper()}** - {wp.difficulty_level.capitalize()} difficulty\n"
            output += f"   - Frequency: {wp.frequency} mentions\n"

            if wp.confusion_indicators > 0:
                output += f"   - Confusion signals: {wp.confusion_indicators}\n"

            if wp.evidence:
                evidence = wp.evidence[0][:80] + "..." if len(wp.evidence[0]) > 80 else wp.evidence[0]
                output += f"   - Example: \"{evidence}\"\n"

            output += "\n"
    else:
        output += "### ✅ Great Session!\nNo significant difficulties detected.\n\n"

    # Priority topics
    if recommendations.priority_topics:
        output += "### 🎯 Priority Topics for Next Session\n"
        for idx, topic in enumerate(recommendations.priority_topics[:3], 1):
            output += f"{idx}. {topic}\n"
        output += "\n"

    # Study time suggestions
    if recommendations.suggested_focus_time:
        output += "### ⏱️ Suggested Study Time\n"
        for topic, minutes in list(recommendations.suggested_focus_time.items())[:3]:
            output += f"- {topic}: {minutes} minutes\n"
        output += "\n"

    # Study tips
    if recommendations.study_approach_tips:
        output += "### 💡 Study Recommendations\n"
        for idx, tip in enumerate(recommendations.study_approach_tips, 1):
            output += f"{idx}. {tip}\n"
        output += "\n"

    output += "\n---\n**Keep up the great work! 🚀**"

    return output


def create_schedule(start_time: str, end_time: str, user_id: str = "default_user"):
    """Create a study schedule based on weak points."""
    try:
        chatbot = get_or_create_chatbot(user_id)

        # Check if we have recommendations
        if chatbot.last_recommendations is None:
            return "⚠️ Please analyze your study session first before creating a schedule."

        if not start_time or not end_time:
            return "❌ Please provide both start and end times (HH:MM format, e.g., 14:00)."

        # Create context for scheduler
        topics = chatbot.last_recommendations.priority_topics[:5] if chatbot.last_recommendations.priority_topics else ["General Study"]

        if not topics:
            topics = ["General Study"]

        # Use the scheduler via chat (LangGraph will route to scheduler agent)
        schedule_request = f"Create a study schedule for tomorrow from {start_time} to {end_time} focusing on: {', '.join(topics)}"
        response = chatbot.chat(schedule_request)

        return f"### 📅 Study Schedule\n\n{response}"

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return f"❌ Error creating schedule: {str(e)}\n\nDetails:\n```\n{error_details}\n```"


def clear_conversation(user_id: str = "default_user"):
    """Clear conversation history."""
    try:
        chatbot = get_or_create_chatbot(user_id)
        result = chatbot.clear_conversation()
        return [], f"✅ {result}"
    except Exception as e:
        return [], f"❌ Error: {str(e)}"


def get_motivation(user_id: str = "default_user"):
    """Get personalized motivation."""
    try:
        from agents.user_profile import UserProfileStore
        from agents.motivator_agent import OpenAIMotivationModel
        from pathlib import Path

        # Check if user has a profile
        profiles_dir = Path("data/profiles")
        profiles_dir.mkdir(parents=True, exist_ok=True)
        profile_store = UserProfileStore(root=profiles_dir)

        try:
            profile = profile_store.load(user_id)
            persona = profile.primary_persona if profile.primary_persona else "motivational coach"
        except FileNotFoundError:
            # If no profile exists, prompt user to create one
            return """
### ⚠️ Profile Not Found

Please create your profile first in the "👤 User Profile" tab to get personalized motivation!

Your profile helps us:
- Choose the right motivational persona for you
- Tailor messages to your goals and challenges
- Track your progress over time
"""

        # Create motivator with profile store and LLM
        motivator = MotivatorAgent(
            profile_store=profile_store,
            llm=OpenAIMotivationModel()
        )

        # Generate personalized motivation
        from agents.quote_scraper import WebSearchQuoteScraper
        scraper = WebSearchQuoteScraper()

        motivation_msg = motivator.craft_personalized_message(
            user_id=user_id,
            scraper=scraper
        )

        return f"### 💪 Motivation from {persona.title()}\n\n{motivation_msg.text}"

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return f"❌ Error: {str(e)}\n\nDetails:\n```\n{error_details}\n```"


def create_gradio_interface():
    """Create the Gradio interface."""

    with gr.Blocks(title="Study Pal - AI Study Assistant", theme=gr.themes.Soft()) as app:
        # Session state to track login
        session_state = gr.State({"logged_in": False, "user_id": None})

        gr.Markdown("""
        # 🎓 Study Pal - Your AI Study Assistant

        Upload your study materials, chat with AI agents, analyze your weak points, and create personalized study schedules!

        **Powered by LangGraph Multi-Agent System**
        """)

        # Login Screen
        with gr.Column(visible=True) as login_screen:
            gr.Markdown("""
            ## 🔐 Welcome to Study Pal

            Please login or create a new account to get started.
            """)

            login_status = gr.Markdown("")

            with gr.Tabs():
                # Login Tab
                with gr.Tab("🔓 Login"):
                    gr.Markdown("""
                    ### Login to Your Account

                    Enter your user ID to access your study materials and continue your learning journey.
                    """)

                    login_user_id = gr.Textbox(
                        label="User ID",
                        placeholder="Enter your user ID (e.g., alice, john_doe)"
                    )
                    login_btn = gr.Button("Login", variant="primary", size="lg")

                # Create Account Tab
                with gr.Tab("✨ Create Account"):
                    gr.Markdown("""
                    ### Create a New Account

                    Fill in the details below to create your personalized study assistant account.
                    """)

                    signup_user_id = gr.Textbox(
                        label="Choose a User ID",
                        placeholder="e.g., alice, john_doe (no spaces)"
                    )
                    signup_name = gr.Textbox(
                        label="Your Name",
                        placeholder="e.g., John Doe"
                    )
                    signup_focus = gr.Textbox(
                        label="Academic Focus",
                        placeholder="e.g., Machine Learning, Physics, Mathematics"
                    )
                    signup_persona = gr.Textbox(
                        label="Motivational Persona (Optional)",
                        placeholder="e.g., Steve Jobs, Richard Feynman",
                        value=""
                    )
                    signup_btn = gr.Button("Create Account", variant="primary", size="lg")

        # Main App (hidden until logged in)
        with gr.Column(visible=False) as main_app:
            # User info bar (logged in)
            with gr.Row():
                logged_user_display = gr.Textbox(
                    label="Logged in as",
                    value="",
                    interactive=False,
                    scale=3
                )
                logout_btn = gr.Button("🚪 Logout", scale=1, variant="secondary")
                status_btn = gr.Button("📊 Get Status", scale=1)

            status_output = gr.Markdown("System ready.")

            # Main tabs
            with gr.Tabs():
                # Tab 1: Upload Materials
                with gr.Tab("📚 Upload Materials"):
                    gr.Markdown("### Upload Study Materials (PDF)")

                    file_upload = gr.File(
                        label="Upload PDF",
                        file_types=[".pdf"],
                        type="filepath"
                    )

                    upload_btn = gr.Button("Upload & Process", variant="primary")

                    upload_status = gr.Textbox(
                        label="Upload Status",
                        interactive=False
                    )

                    with gr.Row():
                        materials_count = gr.Number(
                            label="Total Chunks",
                            value=0,
                            interactive=False
                        )
                        materials_status = gr.Textbox(
                            label="Knowledge Base",
                            value="No materials loaded.",
                            interactive=False
                        )

                # Tab 2: Chat with Tutor
                with gr.Tab("💬 Chat with AI Tutor"):
                    gr.Markdown("""
                    ### Ask Questions About Your Study Materials

                    The AI will automatically route your message to the right agent:
                    - **Study questions** → Tutor Agent (RAG-powered)
                    - **Schedule requests** → Scheduler Agent
                    - **Session analysis** → Analyzer Agent
                    - **Motivation** → Motivator Agent
                    """)

                    chatbot = gr.Chatbot(
                        label="Study Pal Conversation",
                        height=400,
                        type="messages"
                    )

                    with gr.Row():
                        msg = gr.Textbox(
                            label="Your Message",
                            placeholder="Ask a question about your study materials...",
                            scale=4
                        )
                        submit_btn = gr.Button("Send", variant="primary", scale=1)

                    clear_btn = gr.Button("🧹 Clear Conversation")
                    clear_status = gr.Textbox(label="Status", interactive=False)

                    # Example prompts
                    gr.Examples(
                        examples=[
                            "What is machine learning?",
                            "Explain neural networks to me",
                            "I need motivation to study",
                            "Analyze my weak points",
                            "Create a study schedule for tomorrow 2-5pm"
                        ],
                        inputs=msg,
                        label="Example Questions"
                    )

                # Tab 3: Session Analysis
                with gr.Tab("📊 Session Analysis"):
                    gr.Markdown("""
                    ### Analyze Your Study Session

                    Find out which topics you struggled with and get personalized recommendations.
                    """)

                    session_topic = gr.Textbox(
                        label="Session Topic (Optional)",
                        placeholder="e.g., Machine Learning, Neural Networks"
                    )

                    analyze_btn = gr.Button("🔍 Analyze Session", variant="primary")

                    analysis_output = gr.Markdown("No analysis yet. Have a study session first!")

                # Tab 4: Create Schedule
                with gr.Tab("📅 Create Schedule"):
                    gr.Markdown("""
                    ### Create a Study Schedule

                    Based on your weak points, create a personalized study schedule.

                    **Note:** Analyze your session first to get personalized recommendations!
                    """)

                    with gr.Row():
                        start_time = gr.Textbox(
                            label="Start Time",
                            placeholder="14:00",
                            scale=1
                        )
                        end_time = gr.Textbox(
                            label="End Time",
                            placeholder="17:00",
                            scale=1
                        )

                    schedule_btn = gr.Button("📆 Create Schedule", variant="primary")

                    schedule_output = gr.Markdown("No schedule yet. Analyze your session first!")

                # Tab 5: Motivation
                with gr.Tab("💪 Get Motivated"):
                    gr.Markdown("""
                    ### Get Personalized Motivation

                    Receive inspiring messages to boost your study motivation!
                    """)

                    motivation_btn = gr.Button("✨ Get Motivation", variant="primary", size="lg")

                    motivation_output = gr.Markdown("Click the button to get motivated!")

        # Login/Logout Event Handlers
        login_btn.click(
            fn=handle_login,
            inputs=[login_user_id, session_state],
            outputs=[session_state, login_status, login_screen, main_app, logged_user_display]
        )

        signup_btn.click(
            fn=handle_create_account,
            inputs=[signup_user_id, signup_name, signup_persona, signup_focus, session_state],
            outputs=[session_state, login_status, login_screen, main_app, logged_user_display]
        )

        logout_btn.click(
            fn=handle_logout,
            inputs=[session_state],
            outputs=[session_state, login_status, login_screen, main_app, logged_user_display, login_user_id]
        )

        # Event handlers - use logged_user_display as user_id source

        upload_btn.click(
            fn=upload_file,
            inputs=[file_upload, logged_user_display],
            outputs=[upload_status, materials_count, materials_status]
        )

        submit_btn.click(
            fn=chat_with_tutor,
            inputs=[msg, chatbot, logged_user_display],
            outputs=[chatbot, msg]
        )

        msg.submit(
            fn=chat_with_tutor,
            inputs=[msg, chatbot, logged_user_display],
            outputs=[chatbot, msg]
        )

        clear_btn.click(
            fn=clear_conversation,
            inputs=[logged_user_display],
            outputs=[chatbot, clear_status]
        )

        status_btn.click(
            fn=get_system_status,
            inputs=[logged_user_display],
            outputs=[status_output]
        )

        analyze_btn.click(
            fn=analyze_study_session,
            inputs=[session_topic, logged_user_display],
            outputs=[analysis_output]
        )

        schedule_btn.click(
            fn=create_schedule,
            inputs=[start_time, end_time, logged_user_display],
            outputs=[schedule_output]
        )

        motivation_btn.click(
            fn=get_motivation,
            inputs=[logged_user_display],
            outputs=[motivation_output]
        )

    return app


def main():
    """Launch the Gradio app."""
    print("\n" + "=" * 70)
    print("  🎓 STUDY PAL - GRADIO UI")
    print("=" * 70)
    print("\nStarting Gradio interface...")
    print("This will open in your browser automatically.\n")

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  WARNING: OPENAI_API_KEY not found in environment!")
        print("   Make sure you have a .env file with your API key.\n")

    app = create_gradio_interface()

    # Launch with sharing disabled by default (enable with share=True for public URL)
    print("\n🌐 Access the app at:")
    print("   Local:   http://localhost:7860")
    print("   Network: http://127.0.0.1:7860")
    print("\n   Press Ctrl+C to stop\n")

    app.launch(
        server_name="127.0.0.1",  # Use localhost instead of 0.0.0.0
        server_port=7860,
        share=False,  # Set to True to get a public URL
        show_error=True,
        quiet=False
    )


if __name__ == "__main__":
    main()
