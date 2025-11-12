"""Test script for web quote scraping and personalized motivational messages."""

from pathlib import Path
from dotenv import load_dotenv
from agents import (
    MotivatorAgent,
    QuoteStore,
    UserProfile,
    UserProfileStore,
    WebSearchQuoteScraper,
    PersonalizedQuoteGenerator,
)

load_dotenv(override=True)


def setup_user_profile() -> tuple[UserProfileStore, str, UserProfile]:
    """Create a test user with a rich profile."""
    profile_store = UserProfileStore(Path("data/test_profiles"))

    # Create a detailed user profile with multiple personas
    user_id = "test_user_web"
    profile = UserProfile(
        user_id=user_id,
        name="Rom",
        primary_persona="David Goggins",
        preferred_personas=["Isaac Newton", "Marie Curie"],
        study_topics=["Job interviews", "Leetcode", "Personal project"],
        current_focus="scoring a role in hi-tech",
        traits=["procrastination", "doubt", "think little of myself"],
        goals=["finding a job"],
    )

    profile_store.save(profile)
    print(f"✓ Created user profile for {profile.name}")
    print(f"  - Primary persona: {profile.primary_persona}")
    print(f"  - Preferred personas: {', '.join(profile.preferred_personas)}")
    print(f"  - Focus: {profile.current_focus}")
    print(f"  - Traits: {', '.join(profile.traits)}")
    print(f"  - Study topics: {', '.join(profile.study_topics)}\n")

    return profile_store, user_id, profile


def test_quote_scraping(profile: UserProfile):
    """Test 1: Scrape quotes from the web using user's personas."""
    print("=" * 70)
    print("TEST 1: QUOTE SCRAPING FROM USER PERSONAS")
    print("=" * 70)

    # Get personas from user profile instead of hardcoding
    personas = profile.get_personas()
    print(f"\n📋 Using {len(personas)} personas from user profile: {', '.join(personas)}\n")

    scraper = WebSearchQuoteScraper()

    for persona in personas:
        print(f"\n[Scraping quotes for: {persona}]")
        print("-" * 70)

        quotes = scraper.scrape_quotes(persona, limit=2)

        if quotes:
            for i, quote in enumerate(quotes, 1):
                print(f"\nQuote {i}:")
                print(f"  Text: {quote.text}")
                print(f"  Tags: {', '.join(quote.tags)}")
                if quote.source_url:
                    print(f"  Source: {quote.source_url}")
        else:
            print("  ❌ No quotes found")

    print("\n" + "=" * 70)


def test_personalized_generation():
    """Test 2: Generate personalized messages using automatic persona retrieval."""
    print("\n" + "=" * 70)
    print("TEST 2: AUTOMATIC PERSONALIZED MESSAGE GENERATION")
    print("=" * 70)

    # Setup
    profile_store, user_id, profile = setup_user_profile()
    quote_store = QuoteStore(Path("data/quotes_store.json"))

    # Create motivator agent
    motivator = MotivatorAgent(
        profile_store=profile_store,
        quote_store=quote_store,
    )

    print(f"\n🤖 Using craft_messages_from_user_personas() - automatically retrieves personas!\n")

    # Use the new automatic method instead of manually specifying personas
    try:
        messages = motivator.craft_messages_from_user_personas(
            user_id=user_id,
            save_to_store=True,
        )

        print(f"\n✅ Generated {len(messages)} messages!\n")

        # Display all messages
        for i, message in enumerate(messages, 1):
            print(f"\n[Message {i}/{len(messages)} - {message.persona_style}]")
            print("-" * 70)

            print(f"\n{message.text}\n")
            print(f"Source: {message.source}")
            print(f"Persona: {message.persona_style}")
            print(f"User: {message.user_name}")
            print(f"Timestamp: {message.timestamp}")

    except Exception as e:
        import traceback
        print(f"❌ Error: {e}")
        traceback.print_exc()

    print("\n" + "=" * 70)


def test_full_workflow():
    """Test 3: Compare regular vs automatic persona-based message generation."""
    print("\n" + "=" * 70)
    print("TEST 3: COMPARING REGULAR VS AUTOMATIC MESSAGES")
    print("=" * 70)

    # Setup
    profile_store, user_id, profile = setup_user_profile()
    quote_store = QuoteStore(Path("data/quotes_store.json"))

    # Create motivator agent
    from agents import OpenAIMotivationModel
    motivator = MotivatorAgent(
        profile_store=profile_store,
        quote_store=quote_store,
        llm=OpenAIMotivationModel(),
    )

    # Get primary persona from profile
    primary_persona = profile.primary_persona

    # Regular message (using existing quote store)
    print(f"\n[REGULAR MESSAGE - {primary_persona}]")
    print("-" * 70)
    try:
        regular_msg = motivator.craft_message(user_id=user_id, persona=primary_persona)
        print(f"\n{regular_msg.text}\n")
        print(f"Source: {regular_msg.source}")
    except Exception as e:
        print(f"Note: {e}")

    # Web-scraped personalized message using primary persona
    print(f"\n[WEB-SCRAPED MESSAGE - {primary_persona}]")
    print("-" * 70)
    try:
        web_msg = motivator.craft_message_from_web(
            user_id=user_id,
            persona=primary_persona,
            save_to_store=True,
        )
        print(f"\n{web_msg.text}\n")
        print(f"Source: {web_msg.source}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 70)


def main():
    """Run all tests using personas from user profile."""
    print("\n" + "🌟" * 35)
    print("WEB QUOTE SCRAPER & PERSONALIZED MOTIVATOR TEST SUITE")
    print("🌟" * 35 + "\n")

    # Create profile once for all tests
    profile_store, user_id, profile = setup_user_profile()

    # Test 1: Basic quote scraping using profile personas
    test_quote_scraping(profile)

    # Test 2: Automatic personalized message generation
    test_personalized_generation()

    # Test 3: Compare workflows
    test_full_workflow()

    print("\n" + "✅" * 35)
    print("ALL TESTS COMPLETED")
    print("✅" * 35 + "\n")


if __name__ == "__main__":
    main()
