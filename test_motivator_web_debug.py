"""Debug the motivator agent web integration."""

from pathlib import Path
from dotenv import load_dotenv
from agents import MotivatorAgent, QuoteStore, UserProfile, UserProfileStore

load_dotenv(override=True)

def main():
    # Setup profile
    profile_store = UserProfileStore(Path("data/test_profiles"))
    user_id = "test_debug"
    profile = UserProfile(
        user_id=user_id,
        name="Alex",
        primary_persona="Isaac Newton",
        study_topics=["Physics"],
        current_focus="calculus",
        traits=["procrastination"],
        goals=["Master calculus"],
    )
    profile_store.save(profile)

    # Setup quote store
    quote_store = QuoteStore(Path("data/quotes_store.json"))

    # Create motivator
    motivator = MotivatorAgent(
        profile_store=profile_store,
        quote_store=quote_store,
    )

    print("Testing craft_message_from_web...")
    try:
        message = motivator.craft_message_from_web(
            user_id=user_id,
            persona="Isaac Newton",
            save_to_store=False,
        )
        print(f"\nSuccess!")
        print(f"Message:\n{message.text}\n")
        print(f"Source: {message.source}")
    except Exception as e:
        import traceback
        print(f"\nError: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
