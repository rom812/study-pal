"""Interactive onboarding flow for new users."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from agents.user_profile import UserProfile, UserProfileStore


class OnboardingAgent:
    """Guides new users through profile creation with an interactive questionnaire."""

    # Available personas with brief descriptions
    PERSONAS = {
        "Richard Feynman": "Nobel physicist known for simplifying complex ideas with curiosity and humor",
        "Marie Curie": "Pioneer scientist who persevered through obstacles with dedication",
        "Steve Jobs": "Visionary innovator who pushed boundaries and thought differently",
        "Carl Sagan": "Cosmic educator who made science accessible and inspiring",
        "Kobe Bryant": "Elite athlete who embodied relentless work ethic and mental toughness",
        "David Goggins": "Ultra-endurance athlete focused on mental resilience and overcoming limits",
        "Eleanor Roosevelt": "Advocate for growth through facing fears and taking action",
        "Elon Musk": "Entrepreneur tackling ambitious goals through first principles thinking",
        "Jocko Willink": "Navy SEAL emphasizing discipline, ownership, and consistent execution",
        "Isaac Newton": "Mathematical genius who persisted in solving fundamental problems",
        "Niels Bohr": "Quantum physicist who embraced paradox and deep questioning",
        "Travis Kalanick": "Startup founder known for aggressive execution and risk-taking",
    }

    # Common pain points students face
    PAIN_POINTS = [
        "procrastination",
        "perfectionism",
        "burnout",
        "test anxiety",
        "time management",
        "motivation issues",
        "imposter syndrome",
        "information overload",
        "distractions",
        "lack of focus",
    ]

    def __init__(self, profile_store: UserProfileStore):
        """
        Initialize the onboarding agent.

        Args:
            profile_store: Store for persisting user profiles
        """
        self.profile_store = profile_store

    def run_onboarding(self, user_id: str) -> UserProfile:
        """
        Run the complete onboarding flow for a new user.

        Args:
            user_id: Unique identifier for the user

        Returns:
            Newly created UserProfile

        Raises:
            KeyboardInterrupt: If user cancels onboarding
        """
        print("\n" + "=" * 70)
        print("Welcome to Study Pal!")
        print("=" * 70)
        print("\nLet's set up your personalized learning experience.")
        print("This will only take a few minutes.\n")

        try:
            # Collect profile information
            name = self._collect_name()
            primary_persona, selected_personas = self._select_persona()
            academic_field = self._collect_academic_field()
            study_topics = self._collect_study_topics()
            goals = self._collect_goals()
            traits = self._collect_pain_points()

            # Create profile
            profile = UserProfile(
                user_id=user_id,
                name=name,
                primary_persona=primary_persona,
                preferred_personas=selected_personas,
                academic_field=academic_field,
                study_topics=study_topics,
                goals=goals,
                traits=traits,
                current_focus=study_topics[0] if study_topics else None,
            )

            # Save profile
            self.profile_store.save(profile)

            # Success message
            print("\n" + "=" * 70)
            print("Profile Created Successfully!")
            print("=" * 70)
            print(f"\nWelcome, {name}! Your profile has been saved.")
            if len(selected_personas) > 1:
                print(f"Your motivational guides: {', '.join(selected_personas)}")
                print(f"Primary guide: {primary_persona}")
            else:
                print(f"Your motivational guide: {primary_persona}")
            print(f"Focus area: {profile.current_focus or 'Not set'}")
            print("\nYou're all set to start your learning journey!\n")

            return profile

        except KeyboardInterrupt:
            print("\n\nOnboarding cancelled. You can restart anytime.\n")
            raise

    def _collect_name(self) -> str:
        """Collect user's name."""
        while True:
            name = input("What's your name? ").strip()
            if name:
                return name
            print("Please enter your name.")

    def _select_persona(self) -> tuple[str, list[str]]:
        """
        Display available personas and let user choose or create their own.
        Supports multiple personas separated by commas.

        Returns:
            Tuple of (primary_persona, list of all selected personas)
        """
        print("\n" + "-" * 70)
        print("Choose Your Motivational Guide(s)")
        print("-" * 70)
        print("\nWho inspires you? Pick persona(s) for personalized motivation:\n")

        # Display personas with numbers
        personas_list = list(self.PERSONAS.items())
        for idx, (persona, description) in enumerate(personas_list, 1):
            print(f"{idx:2}. {persona}")
            print(f"    {description}\n")

        print(f"{len(personas_list) + 1:2}. Create my own custom persona(s)\n")

        # Get selection
        while True:
            print("You can:")
            print("  - Select one or more numbers separated by commas (e.g., 1,5,8)")
            print(f"  - Choose option {len(personas_list) + 1} to create your own persona(s)")
            choice = input("\nYour choice: ").strip()

            if not choice:
                print("Please make a selection.\n")
                continue

            # Check if user wants to create custom persona(s)
            if choice == str(len(personas_list) + 1):
                return self._create_custom_personas()

            # Try to parse as numbers (for predefined personas)
            try:
                indices = [int(x.strip()) - 1 for x in choice.split(",")]
                selected_personas = []

                for idx in indices:
                    if 0 <= idx < len(personas_list):
                        selected_personas.append(personas_list[idx][0])
                    else:
                        print(f"Invalid number: {idx + 1}. Please use numbers between 1 and {len(personas_list)}.\n")
                        break
                else:
                    # All indices were valid
                    if selected_personas:
                        primary = selected_personas[0]
                        print(f"\nGreat choice! Your guide(s): {', '.join(selected_personas)}")
                        print(f"Primary persona: {primary}\n")
                        return primary, selected_personas
                    else:
                        print("No valid personas selected.\n")
            except ValueError:
                print("Invalid input. Please enter numbers separated by commas or select the custom option.\n")

    def _create_custom_personas(self) -> tuple[str, list[str]]:
        """
        Allow user to create their own custom persona(s).

        Returns:
            Tuple of (primary_persona, list of all custom personas)
        """
        print("\n" + "-" * 70)
        print("Create Custom Persona(s)")
        print("-" * 70)
        print("\nDefine your own motivational guide(s)!")
        print("You can enter:")
        print("  - A single persona (e.g., 'Marcus Aurelius')")
        print("  - Multiple personas separated by commas (e.g., 'Marcus Aurelius, Bruce Lee, Maya Angelou')")
        print("  - Any person, character, or archetype that inspires you\n")

        while True:
            custom_input = input("Enter your persona(s): ").strip()

            if not custom_input:
                print("Please enter at least one persona name.\n")
                continue

            # Parse comma-separated personas
            personas = [p.strip() for p in custom_input.split(",") if p.strip()]

            if not personas:
                print("Please enter at least one valid persona name.\n")
                continue

            # Remove duplicates while preserving order
            seen = set()
            unique_personas = []
            for persona in personas:
                if persona.lower() not in seen:
                    seen.add(persona.lower())
                    unique_personas.append(persona)

            primary = unique_personas[0]

            print(f"\nCustom persona(s) created: {', '.join(unique_personas)}")
            print(f"Primary persona: {primary}\n")

            # Confirm with user
            confirm = input("Is this correct? (yes/no): ").strip().lower()
            if confirm in ["yes", "y"]:
                return primary, unique_personas
            else:
                print("\nLet's try again.\n")

    def _collect_academic_field(self) -> Optional[str]:
        """
        Collect user's academic field.

        Returns:
            Academic field or None if skipped
        """
        print("-" * 70)
        print("Academic Field")
        print("-" * 70)
        field = input(
            "What field are you studying? (e.g., Computer Science, Math, Physics)\n[Press Enter to skip]: "
        ).strip()
        return field if field else None

    def _collect_study_topics(self) -> list[str]:
        """
        Collect list of topics the user is currently studying.

        Returns:
            List of study topics (may be empty)
        """
        print("\n" + "-" * 70)
        print("Current Study Topics")
        print("-" * 70)
        print("What topics or subjects are you currently learning?")
        print("Enter one topic per line. Press Enter twice when done.\n")

        topics = []
        while True:
            topic = input(f"Topic {len(topics) + 1}: ").strip()
            if not topic:
                if topics or len(topics) == 0:
                    break
            else:
                topics.append(topic)
                if len(topics) >= 10:
                    print("(Maximum 10 topics reached)")
                    break

        if topics:
            print(f"\nAdded {len(topics)} topic(s): {', '.join(topics)}\n")
        else:
            print("No topics added. You can add them later.\n")

        return topics

    def _collect_goals(self) -> list[str]:
        """
        Collect user's learning goals.

        Returns:
            List of goals (may be empty)
        """
        print("-" * 70)
        print("Learning Goals")
        print("-" * 70)
        print("What do you want to achieve with your studies?")
        print("Examples: 'Pass calculus exam', 'Master Python', 'Ace my finals'")
        print("Enter one goal per line. Press Enter twice when done.\n")

        goals = []
        while True:
            goal = input(f"Goal {len(goals) + 1}: ").strip()
            if not goal:
                if goals or len(goals) == 0:
                    break
            else:
                goals.append(goal)
                if len(goals) >= 10:
                    print("(Maximum 10 goals reached)")
                    break

        if goals:
            print(f"\nAdded {len(goals)} goal(s)\n")
        else:
            print("No goals added. You can set them later.\n")

        return goals

    def _collect_pain_points(self) -> list[str]:
        """
        Collect user's pain points or challenges.

        Returns:
            List of selected pain points
        """
        print("-" * 70)
        print("Study Challenges")
        print("-" * 70)
        print("What challenges do you face? (Select all that apply)\n")

        # Display pain points with numbers
        for idx, pain_point in enumerate(self.PAIN_POINTS, 1):
            print(f"{idx:2}. {pain_point}")

        print("\nEnter numbers separated by commas (e.g., 1,3,5)")
        print("Or press Enter to skip: ")

        selection = input().strip()

        if not selection:
            print("No challenges selected.\n")
            return []

        # Parse selection
        selected_traits = []
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(",")]
            for idx in indices:
                if 0 <= idx < len(self.PAIN_POINTS):
                    selected_traits.append(self.PAIN_POINTS[idx])

            if selected_traits:
                print(f"\nSelected challenges: {', '.join(selected_traits)}\n")
            else:
                print("No valid challenges selected.\n")

        except ValueError:
            print("Invalid input. No challenges added.\n")

        return selected_traits


def create_onboarding_agent(profiles_dir: Path = Path("data/profiles")) -> OnboardingAgent:
    """
    Factory function to create an OnboardingAgent with default settings.

    Args:
        profiles_dir: Directory where user profiles are stored

    Returns:
        Configured OnboardingAgent instance
    """
    profile_store = UserProfileStore(profiles_dir)
    return OnboardingAgent(profile_store)
