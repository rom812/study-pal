"""
Complete End-to-End Workflow Test (Automated)

This script automatically tests the full Study Pal workflow:
1. Onboarding (create user profile)
2. Motivator (personalized message)
3. Tutor Agent (quiz/study session)
4. Weakness Analyzer (evaluate performance)
5. Scheduler (create next session based on weak points)
"""

from pathlib import Path
from dotenv import load_dotenv
from core.langgraph_chatbot import LangGraphChatbot
from agents.user_profile import UserProfileStore, UserProfile
from agents.motivator_agent import MotivatorAgent, OpenAIMotivationModel
from agents.scheduler_agent import SchedulerAgent
from core.mcp_connectors import CalendarConnector
import time

# Load environment variables from .env file
load_dotenv(override=True)


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def step_1_onboarding():
    """Step 1: Create/load user profile."""
    print_section("STEP 1: USER ONBOARDING")

    user_id = "non-existent"
    profile_store = UserProfileStore(Path("data/profiles"))

    # Check if profile exists
    try:
        profile = profile_store.load(user_id)
        print(f"✅ Loaded existing profile for: {profile.name}")
        print(f"   Persona: {profile.primary_persona}")
        print(f"   Focus: {profile.current_focus}")
    except FileNotFoundError:
        # Create a new profile
        print("Creating new user profile...")
        profile = UserProfile(
            user_id=user_id,
            name="Test Student",
            primary_persona="Adam Sandler",
            current_focus="AI",
            goals=["Finding a job", "Build AI projects"],
            traits=["procrastination", "Staying Focused"],
            study_topics=["MongoDB", "Multi-agent systems", "LangGraph"]
        )
        profile_store.save(profile)
        print(f"✅ Created new profile for: {profile.name}")
        print(f"   Persona: {profile.primary_persona}")
        print(f"   Focus: {profile.current_focus}")

    return profile


def step_2_motivator(profile: UserProfile):
    """Step 2: Get personalized motivational message."""
    print_section("STEP 2: MOTIVATOR AGENT - Personalized Message")

    # Create profile store
    profile_store = UserProfileStore(Path("data/profiles"))

    # Create motivator with simplified API
    motivator = MotivatorAgent(
        profile_store=profile_store,
        llm=OpenAIMotivationModel()
    )

    # Generate personalized motivation using new API
    print(f"Generating motivation in the style of {profile.primary_persona}...")
    print(f"  - Scraping quotes from the web...")
    print(f"  - Crafting personalized message for {profile.name}...")

    motivation = motivator.craft_personalized_message(
        user_id=profile.user_id
    )

    print(f"\n💪 {motivation.text}")
    print(f"\n✅ Motivational message delivered!")

    return motivation


def step_3_tutor_session(profile: UserProfile):
    """Step 3: Run tutoring session with quiz."""
    print_section("STEP 3: TUTOR AGENT - Study Session")

    # Create chatbot
    chatbot = LangGraphChatbot(user_id=profile.user_id, session_id="workflow_test")

    print("Starting tutoring session...")

    # Simulate a study session with questions
    print("\n📚 Student asks questions about study materials...\n")

    questions = [
        "create a quiz for me please",
        "1.b 2.b 3.b 4.a 5.b 6.a",  # Quiz answers
        "I don't really understand the AutoGen part",
        "Can you explain multi-agent systems again?",
        "wow i cant understand this!"
    ]

    for i, question in enumerate(questions, 1):
        print(f"💭 Student: {question}")
        response = chatbot.chat(question)
        print(f"🎓 Tutor: {response[:200]}...")
        if len(response) > 200:
            print("   [response truncated]")
        print()

    print("✅ Tutoring session complete!")

    return chatbot


def step_4_weakness_analysis(chatbot: LangGraphChatbot):
    """Step 4: Analyze session to identify weak points."""
    print_section("STEP 4: WEAKNESS ANALYZER - Evaluate Performance")

    print("Analyzing study session to identify weak points...\n")

    # Analyze the session
    recommendations = chatbot.analyze_session(session_topic="Multi-agent systems and AutoGen")

    # Display analysis results
    print("📊 SESSION ANALYSIS RESULTS")
    print("-" * 80)

    print(f"\n📝 Summary: {recommendations.session_summary}\n")

    if recommendations.weak_points:
        print(f"🎯 Weak Points Identified: {len(recommendations.weak_points)}")
        print("-" * 80)

        for idx, wp in enumerate(recommendations.weak_points, 1):
            # Difficulty indicator
            if wp.difficulty_level == "severe":
                icon = "🔴"
            elif wp.difficulty_level == "moderate":
                icon = "🟡"
            else:
                icon = "🟢"

            print(f"\n{idx}. {icon} {wp.topic.upper()}")
            print(f"   Difficulty: {wp.difficulty_level}")
            print(f"   Frequency: {wp.frequency} mention(s)")

            if wp.evidence:
                print(f"   Evidence: \"{wp.evidence[0][:100]}...\"")

    # Priority topics
    if recommendations.priority_topics:
        print(f"\n🎯 Priority Topics for Next Session:")
        for idx, topic in enumerate(recommendations.priority_topics[:3], 1):
            print(f"   {idx}. {topic}")

    # Suggested focus time
    if recommendations.suggested_focus_time:
        print(f"\n⏱️  Recommended Study Time:")
        for topic, minutes in list(recommendations.suggested_focus_time.items())[:3]:
            print(f"   • {topic}: {minutes} minutes")

    # Study tips
    if recommendations.study_approach_tips:
        print(f"\n💡 Study Recommendations:")
        for idx, tip in enumerate(recommendations.study_approach_tips[:3], 1):
            print(f"   {idx}. {tip}")

    print("\n" + "-" * 80)
    print("✅ Weakness analysis complete!")

    return recommendations


def step_5_scheduler(profile: UserProfile, recommendations):
    """Step 5: Create study schedule based on weak points."""
    print_section("STEP 5: SCHEDULER AGENT - Create Next Session")

    print("Creating personalized study schedule based on weak points...\n")

    # Create scheduler
    calendar_connector = CalendarConnector()
    scheduler = SchedulerAgent(calendar_connector=calendar_connector)

    # Build context with user availability
    context = {
        "user_input": "I'm available from 14:00 to 16:00 tomorrow",
        "user_id": profile.user_id
    }

    # Generate schedule with weak points prioritization
    schedule = scheduler.generate_schedule(
        context=context,
        recommendations=recommendations
    )

    # Display schedule
    print("📅 TOMORROW'S STUDY SCHEDULE")
    print("-" * 80)

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
    study_count = len([s for s in sessions if s['type'] == 'study'])
    print(f"\n📚 Study Sessions ({study_count} Pomodoro blocks):")
    print("-" * 80)

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

    print("-" * 80)

    # Attempt to sync to Google Calendar
    print("\n📆 Syncing schedule to Google Calendar...")
    try:
        scheduler.sync_schedule(schedule)
        print("✅ Schedule synced to Google Calendar!")
    except Exception as e:
        print(f"⚠️  Calendar sync skipped: {e}")
        print("   To enable calendar sync, configure GOOGLE_CALENDAR_MCP_URL in .env")

    return schedule


def main():
    """Run the complete workflow."""
    print("\n" + "=" * 80)
    print("  🎓 STUDY PAL - COMPLETE WORKFLOW TEST (AUTOMATED)")
    print("=" * 80)
    print("\nTesting full workflow:")
    print("  Onboarding → Motivator → Tutor → Analyzer → Scheduler")
    print()

    try:
        # Step 1: Onboarding
        profile = step_1_onboarding()

        # Step 2: Motivator
        motivation = step_2_motivator(profile)

        # Step 3: Tutor Session
        chatbot = step_3_tutor_session(profile)

        # Step 4: Weakness Analysis
        recommendations = step_4_weakness_analysis(chatbot)

        # Step 5: Scheduler
        schedule = step_5_scheduler(profile, recommendations)

        # Final summary
        print_section("✅ WORKFLOW COMPLETE!")

        print("Summary of workflow execution:")
        print(f"  1. ✅ User profile: {profile.name} ({profile.primary_persona})")
        print(f"  2. ✅ Motivation delivered in {profile.primary_persona}'s style")
        print(f"  3. ✅ Tutoring session completed with {len(chatbot.memory.messages)} messages")
        print(f"  4. ✅ Identified {len(recommendations.weak_points)} weak points")
        print(f"  5. ✅ Created schedule with {len(schedule['sessions'])} sessions")
  
        print("\n" + "=" * 80)
        print("  🎉 All components working together successfully!")
        print("=" * 80 + "\n")

        return True

    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
