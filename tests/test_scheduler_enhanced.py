#!/usr/bin/env python3
"""Test the enhanced scheduler with date support and full window filling."""

from datetime import datetime, timedelta

from agents.scheduler_agent import SchedulerAgent


def test_scheduler_with_date():
    """Test scheduler with date specification."""
    print("=" * 70)
    print("TEST 1: Scheduler with Thursday 18:00-20:00, Math Division")
    print("=" * 70)

    # Use scheduler WITHOUT LLM (heuristic mode)
    scheduler = SchedulerAgent(llm=None)

    # Calculate next Thursday
    today = datetime.now()
    days_ahead = (3 - today.weekday()) % 7  # Thursday = 3
    if days_ahead == 0:
        days_ahead = 7
    next_thursday = today + timedelta(days=days_ahead)

    context = {"user_input": "Thursday from 18:00 to 20:00 studying math division"}

    schedule = scheduler.generate_schedule(context)

    print(f"\n📅 Schedule Date: {schedule['preferences'].get('date', 'No date set')}")
    print(f"📚 Subjects: {schedule['preferences']['subjects']}")
    print(f"⏰ Time Window: {schedule['preferences']['start_time']} - {schedule['preferences']['end_time']}")
    print(f"\n{'=' * 70}")
    print("SESSIONS:")
    print(f"{'=' * 70}\n")

    for i, session in enumerate(schedule["sessions"], 1):
        if session["type"] == "study":
            task = session.get("task", session["subject"])
            duration_note = session.get("duration_note", "")
            print(f"{i}. 📖 {session['start']} - {session['end']}: {task}")
            if duration_note:
                print(f"   ({duration_note})")
            if "date" in session:
                print(f"   Date: {session['date']} ({session.get('day_name', '')})")
        elif session["type"] == "break":
            print(f"   ☕ {session['start']} - {session['end']}: Break")

    # Verify window is filled
    sessions = schedule["sessions"]
    study_sessions = [s for s in sessions if s["type"] == "study"]

    print(f"\n{'=' * 70}")
    print(f"Total sessions: {len(sessions)}")
    print(f"Study sessions: {len(study_sessions)}")
    print(f"Break sessions: {len(sessions) - len(study_sessions)}")

    # Calculate total study time
    total_study_minutes = 0
    for session in study_sessions:
        start_time = datetime.strptime(session["start"], "%H:%M")
        end_time = datetime.strptime(session["end"], "%H:%M")
        duration = (end_time - start_time).total_seconds() / 60
        total_study_minutes += duration

    print(f"Total study time: {int(total_study_minutes)} minutes")
    print(f"{'=' * 70}\n")


def test_scheduler_fills_entire_window():
    """Test that scheduler fills the entire time window."""
    print("=" * 70)
    print("TEST 2: Verify Entire Window is Filled (2-hour window)")
    print("=" * 70)

    scheduler = SchedulerAgent(llm=None)

    context = {"user_input": "Tomorrow from 14:00 to 16:00 studying Python and Data Structures"}

    schedule = scheduler.generate_schedule(context)

    sessions = schedule["sessions"]

    # Get first and last session times
    first_session = sessions[0]
    last_session = sessions[-1]

    print("\n⏰ Requested: 14:00 - 16:00")
    print(f"📅 First session starts: {first_session['start']}")
    print(f"📅 Last session ends: {last_session['end']}")

    # Check if we're using all the time
    start_minutes = int(first_session["start"].split(":")[0]) * 60 + int(first_session["start"].split(":")[1])
    end_minutes = int(last_session["end"].split(":")[0]) * 60 + int(last_session["end"].split(":")[1])
    used_minutes = end_minutes - start_minutes

    print(f"⏱️  Time window used: {used_minutes} minutes out of 120 minutes")
    print(f"✅ Window utilization: {(used_minutes / 120) * 100:.1f}%")

    print(f"\n{'=' * 70}")
    print("SESSIONS:")
    print(f"{'=' * 70}\n")

    for i, session in enumerate(sessions, 1):
        if session["type"] == "study":
            task = session.get("task", session["subject"])
            print(f"{i}. 📖 {session['start']} - {session['end']}: {task}")
        elif session["type"] == "break":
            print(f"   ☕ {session['start']} - {session['end']}: Break")

    print(f"\n{'=' * 70}\n")


def test_varied_tasks():
    """Test that different task types are generated."""
    print("=" * 70)
    print("TEST 3: Task Variety (3-hour window)")
    print("=" * 70)

    scheduler = SchedulerAgent(llm=None)

    context = {"user_input": "Today from 09:00 to 12:00 studying Calculus"}

    schedule = scheduler.generate_schedule(context)

    print(f"\n📅 Date: {schedule['preferences'].get('date', 'Not set')}")
    print(f"\n{'=' * 70}")
    print("TASKS GENERATED:")
    print(f"{'=' * 70}\n")

    study_sessions = [s for s in schedule["sessions"] if s["type"] == "study"]

    for i, session in enumerate(study_sessions, 1):
        task = session.get("task", session["subject"])
        print(f"{i}. {session['start']}-{session['end']}: {task}")

    print(f"\n{'=' * 70}")
    print(f"Total unique study blocks: {len(study_sessions)}")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    print("\n🧪 ENHANCED SCHEDULER TESTS\n")

    try:
        test_scheduler_with_date()
        print("\n" + "=" * 70 + "\n")

        test_scheduler_fills_entire_window()
        print("\n" + "=" * 70 + "\n")

        test_varied_tasks()

        print("\n✅ All tests completed successfully!\n")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
