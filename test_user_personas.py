"""Test script demonstrating automatic persona retrieval from user profile."""

from pathlib import Path
from dotenv import load_dotenv
from agents import (
    MotivatorAgent,
    QuoteStore,
    UserProfile,
    UserProfileStore,
)

load_dotenv(override=True)


def main():
    """
    Demonstrate how the motivator automatically generates messages
    from all personas defined in the user's profile.
    """
    print("=" * 70)
    print("USER PROFILE PERSONAS - AUTOMATIC MESSAGE GENERATION")
    print("=" * 70)

    # Setup
    profile_store = UserProfileStore(Path("data/profiles"))
    quote_store = QuoteStore(Path("data/quotes_store.json"))

    # Create user profile with multiple personas
    user_id = "rom_test"
    profile = UserProfile(
        user_id=user_id,
        name="Rom",
        primary_persona="David Goggins",
        preferred_personas=[
            "Jocko Willink",
            "Steve Jobs",
            "Elon Musk",
        ],
        study_topics=["Job interviews", "Leetcode", "Personal projects"],
        current_focus="scoring a role in hi-tech",
        traits=["procrastination", "doubt", "think little of myself"],
        goals=["Finding a job", "Building confidence", "Mastering interviews"],
    )

    profile_store.save(profile)

    print(f"\n✓ Created profile for: {profile.name}")
    print(f"  Primary persona: {profile.primary_persona}")
    print(f"  Preferred personas: {', '.join(profile.preferred_personas)}")
    print(f"  Focus: {profile.current_focus}")
    print(f"  Traits: {', '.join(profile.traits)}")
    print(f"  Goals: {', '.join(profile.goals)}\n")

    # Test get_personas method
    all_personas = profile.get_personas()
    print(f"📋 Retrieved {len(all_personas)} personas from profile:")
    for i, persona in enumerate(all_personas, 1):
        print(f"   {i}. {persona}")
    print()

    # Create motivator
    motivator = MotivatorAgent(
        profile_store=profile_store,
        quote_store=quote_store,
    )

    print("=" * 70)
    print("GENERATING PERSONALIZED MESSAGES FROM ALL PERSONAS")
    print("=" * 70)

    # Generate messages from all user personas automatically
    messages = motivator.craft_messages_from_user_personas(
        user_id=user_id,
        save_to_store=True,
    )

    print(f"\n✅ Successfully generated {len(messages)} messages!\n")

    # Display all messages
    for i, message in enumerate(messages, 1):
        print("\n" + "=" * 70)
        print(f"MESSAGE {i}/{len(messages)} - {message.persona_style}")
        print("=" * 70)
        print(f"\n{message.text}\n")
        print(f"Source: {message.source}")
        print(f"Timestamp: {message.timestamp}")
        print("=" * 70)

    print("\n" + "✅" * 35)
    print("DEMO COMPLETE")
    print("✅" * 35)

    print("\n💡 Key Features Demonstrated:")
    print("   1. User profile stores primary + preferred personas")
    print("   2. get_personas() retrieves all personas automatically")
    print("   3. craft_messages_from_user_personas() generates messages for all")
    print("   4. No need to manually specify personas - they come from the profile!")


if __name__ == "__main__":
    main()
