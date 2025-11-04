"""Simple example showing how to use the web quote scraper and personalized motivator."""

from pathlib import Path
from dotenv import load_dotenv
from agents import (
    MotivatorAgent,
    QuoteStore,
    UserProfile,
    UserProfileStore,
)

# Load environment variables (OPENAI_API_KEY)
load_dotenv(override=True)


def main():
    """
    Example: Generate a personalized motivational message by scraping quotes
    from the web for a specific persona.
    """

    # Setup user profile
    print("Setting up user profile...")
    profile_store = UserProfileStore(Path("data/profiles"))
    user_id = "example_user"

    # Create or load user profile
    profile = UserProfile(
        user_id=user_id,
        name="Jordan",
        primary_persona="Albert Einstein",
        study_topics=["Mathematics", "Physics", "Quantum Mechanics"],
        current_focus="understanding quantum entanglement",
        traits=["curious", "sometimes overwhelmed"],
        goals=[
            "Master quantum mechanics fundamentals",
            "Build intuition for complex concepts",
        ],
    )
    profile_store.save(profile)
    print(f"✓ Profile created for {profile.name}\n")

    # Setup quote store
    quote_store = QuoteStore(Path("data/quotes_store.json"))

    # Create motivator agent
    motivator = MotivatorAgent(
        profile_store=profile_store,
        quote_store=quote_store,
    )

    # Choose a persona to get inspiration from
    persona = "Niels Bohr"  # Change this to any historical figure!

    print(f"Generating personalized motivational message from {persona}...")
    print("This will:")
    print("  1. Scrape inspirational quotes from the web")
    print("  2. Create a deeply personalized message based on your profile")
    print("  3. Connect the persona's struggles to your journey\n")
    print("=" * 70)

    # Generate the message
    message = motivator.craft_message_from_web(
        user_id=user_id,
        persona=persona,
        save_to_store=True,  # Save the quote for future use
    )

    # Display the result
    print("\n" + "=" * 70)
    print(f"PERSONALIZED MESSAGE FROM {persona.upper()}")
    print("=" * 70)
    print(f"\n{message.text}\n")
    print("=" * 70)
    print(f"Source: {message.source}")
    print(f"User: {message.user_name}")
    print(f"Generated at: {message.timestamp}")
    print("=" * 70)

    # You can try different personas too!
    print("\n\nTry these other personas by changing the 'persona' variable:")
    print("  - Isaac Newton")
    print("  - Marie Curie")
    print("  - Richard Feynman")
    print("  - Carl Sagan")
    print("  - Albert Einstein")
    print("  - Ada Lovelace")
    print("  - Stephen Hawking")
    print("  - Or any other inspirational figure!")


if __name__ == "__main__":
    main()
