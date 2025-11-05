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


def setup_user_profile() -> tuple[UserProfileStore, str]:
    """Create a test user with a rich profile."""
    profile_store = UserProfileStore(Path("data/test_profiles"))

    # Create a detailed user profile
    user_id = "test_user_web"
    profile = UserProfile(
        user_id=user_id,
        name="Rom",
        primary_persona="David goggins",
        study_topics=["Job interviews", "Leetcode", "Personal project"],
        current_focus="scoring a role in hi-tech",
        traits=["procrastination", "doubt", "think little of myslf"],
        goals=["finding a job"],
    )

    profile_store.save(profile)
    print(f"✓ Created user profile for {profile.name}")
    print(f"  - Focus: {profile.current_focus}")
    print(f"  - Traits: {', '.join(profile.traits)}")
    print(f"  - Study topics: {', '.join(profile.study_topics)}\n")

    return profile_store, user_id


def test_quote_scraping():
    """Test 1: Scrape quotes from the web."""
    print("=" * 70)
    print("TEST 1: QUOTE SCRAPING")
    print("=" * 70)

    scraper = WebSearchQuoteScraper()
    personas = ["Isaac Newton", "Marie Curie", "Albert Einstein"]

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
    """Test 2: Generate personalized messages with scraped quotes."""
    print("\n" + "=" * 70)
    print("TEST 2: PERSONALIZED MESSAGE GENERATION")
    print("=" * 70)

    # Setup
    profile_store, user_id = setup_user_profile()
    quote_store = QuoteStore(Path("data/quotes_store.json"))

    # Create motivator agent
    motivator = MotivatorAgent(
        profile_store=profile_store,
        quote_store=quote_store,
    )

    # Test with different personas
    test_personas = [
        "Isaac Newton",
        "Marie Curie",
        "Richard Feynman",
    ]

    for persona in test_personas:
        print(f"\n[Generating personalized message for: {persona}]")
        print("-" * 70)

        try:
            message = motivator.craft_message_from_web(
                user_id=user_id,
                persona=persona,
                save_to_store=True,
            )

            print(f"\n{message.text}\n")
            print(f"Source: {message.source}")
            print(f"Persona: {message.persona_style}")
            print(f"User: {message.user_name}")
            print(f"Timestamp: {message.timestamp}")

        except Exception as e:
            import traceback
            print(f"❌ Error: {e}")
            traceback.print_exc()

        print("-" * 70)

    print("\n" + "=" * 70)


def test_full_workflow():
    """Test 3: Complete workflow - scrape, personalize, and compare with regular message."""
    print("\n" + "=" * 70)
    print("TEST 3: COMPARING REGULAR VS WEB-SCRAPED MESSAGES")
    print("=" * 70)

    # Setup
    profile_store, user_id = setup_user_profile()
    quote_store = QuoteStore(Path("data/quotes_store.json"))

    # Create motivator agent
    from agents import OpenAIMotivationModel
    motivator = MotivatorAgent(
        profile_store=profile_store,
        quote_store=quote_store,
        llm=OpenAIMotivationModel(),
    )

    persona = "Carl Sagan"

    # Regular message (using existing quote store)
    print(f"\n[REGULAR MESSAGE - {persona}]")
    print("-" * 70)
    try:
        regular_msg = motivator.craft_message(user_id=user_id, persona=persona)
        print(f"\n{regular_msg.text}\n")
        print(f"Source: {regular_msg.source}")
    except Exception as e:
        print(f"Note: {e}")

    # Web-scraped personalized message
    print(f"\n[WEB-SCRAPED PERSONALIZED MESSAGE - {persona}]")
    print("-" * 70)
    try:
        web_msg = motivator.craft_message_from_web(
            user_id=user_id,
            persona=persona,
            save_to_store=True,
        )
        print(f"\n{web_msg.text}\n")
        print(f"Source: {web_msg.source}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 70)


def main():
    """Run all tests."""
    print("\n" + "🌟" * 35)
    print("WEB QUOTE SCRAPER & PERSONALIZED MOTIVATOR TEST SUITE")
    print("🌟" * 35 + "\n")

    # Test 1: Basic quote scraping
    test_quote_scraping()

    # Test 2: Personalized message generation
    test_personalized_generation()

    # Test 3: Compare workflows
    test_full_workflow()

    print("\n" + "✅" * 35)
    print("ALL TESTS COMPLETED")
    print("✅" * 35 + "\n")


if __name__ == "__main__":
    main()
