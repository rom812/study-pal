"""Tests for the onboarding agent."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agents.onboarding import OnboardingAgent
from agents.user_profile import UserProfile, UserProfileStore


@pytest.fixture
def temp_profiles_dir(tmp_path):
    """Create a temporary directory for user profiles."""
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    return profiles_dir


@pytest.fixture
def profile_store(temp_profiles_dir):
    """Create a UserProfileStore with temporary directory."""
    return UserProfileStore(temp_profiles_dir)


@pytest.fixture
def onboarding_agent(profile_store):
    """Create an OnboardingAgent instance."""
    return OnboardingAgent(profile_store)


class TestOnboardingAgent:
    """Test suite for OnboardingAgent."""

    def test_personas_available(self, onboarding_agent):
        """Test that personas are defined."""
        assert len(OnboardingAgent.PERSONAS) > 0
        assert "Richard Feynman" in OnboardingAgent.PERSONAS
        assert "Marie Curie" in OnboardingAgent.PERSONAS
        assert "Steve Jobs" in OnboardingAgent.PERSONAS

    def test_pain_points_available(self, onboarding_agent):
        """Test that pain points are defined."""
        assert len(OnboardingAgent.PAIN_POINTS) > 0
        assert "procrastination" in OnboardingAgent.PAIN_POINTS
        assert "perfectionism" in OnboardingAgent.PAIN_POINTS
        assert "burnout" in OnboardingAgent.PAIN_POINTS

    @patch("builtins.input")
    def test_collect_name(self, mock_input, onboarding_agent):
        """Test name collection."""
        mock_input.return_value = "Alice"
        name = onboarding_agent._collect_name()
        assert name == "Alice"

    @patch("builtins.input")
    def test_collect_name_retry_on_empty(self, mock_input, onboarding_agent):
        """Test that name collection retries on empty input."""
        mock_input.side_effect = ["", "  ", "Bob"]
        name = onboarding_agent._collect_name()
        assert name == "Bob"
        assert mock_input.call_count == 3

    @patch("builtins.input")
    def test_select_persona(self, mock_input, onboarding_agent):
        """Test persona selection."""
        mock_input.return_value = "1"  # Select first persona
        persona = onboarding_agent._select_persona()
        assert persona in OnboardingAgent.PERSONAS

    @patch("builtins.input")
    def test_select_persona_invalid_then_valid(self, mock_input, onboarding_agent):
        """Test persona selection with invalid input first."""
        mock_input.side_effect = ["99", "0", "abc", "1"]
        persona = onboarding_agent._select_persona()
        assert persona in OnboardingAgent.PERSONAS

    @patch("builtins.input")
    def test_collect_academic_field(self, mock_input, onboarding_agent):
        """Test academic field collection."""
        mock_input.return_value = "Computer Science"
        field = onboarding_agent._collect_academic_field()
        assert field == "Computer Science"

    @patch("builtins.input")
    def test_collect_academic_field_skip(self, mock_input, onboarding_agent):
        """Test skipping academic field."""
        mock_input.return_value = ""
        field = onboarding_agent._collect_academic_field()
        assert field is None

    @patch("builtins.input")
    def test_collect_study_topics(self, mock_input, onboarding_agent):
        """Test study topics collection."""
        mock_input.side_effect = ["Python", "Machine Learning", ""]
        topics = onboarding_agent._collect_study_topics()
        assert topics == ["Python", "Machine Learning"]

    @patch("builtins.input")
    def test_collect_study_topics_empty(self, mock_input, onboarding_agent):
        """Test collecting no topics."""
        mock_input.return_value = ""
        topics = onboarding_agent._collect_study_topics()
        assert topics == []

    @patch("builtins.input")
    def test_collect_goals(self, mock_input, onboarding_agent):
        """Test goals collection."""
        mock_input.side_effect = ["Pass exam", "Learn Python", ""]
        goals = onboarding_agent._collect_goals()
        assert goals == ["Pass exam", "Learn Python"]

    @patch("builtins.input")
    def test_collect_goals_empty(self, mock_input, onboarding_agent):
        """Test collecting no goals."""
        mock_input.return_value = ""
        goals = onboarding_agent._collect_goals()
        assert goals == []

    @patch("builtins.input")
    def test_collect_pain_points(self, mock_input, onboarding_agent):
        """Test pain points collection."""
        mock_input.return_value = "1,2,3"
        traits = onboarding_agent._collect_pain_points()
        assert len(traits) == 3
        assert all(trait in OnboardingAgent.PAIN_POINTS for trait in traits)

    @patch("builtins.input")
    def test_collect_pain_points_skip(self, mock_input, onboarding_agent):
        """Test skipping pain points."""
        mock_input.return_value = ""
        traits = onboarding_agent._collect_pain_points()
        assert traits == []

    @patch("builtins.input")
    def test_collect_pain_points_invalid(self, mock_input, onboarding_agent):
        """Test invalid pain points input."""
        mock_input.return_value = "abc,xyz"
        traits = onboarding_agent._collect_pain_points()
        assert traits == []

    @patch("builtins.input")
    def test_full_onboarding_flow(self, mock_input, onboarding_agent, temp_profiles_dir):
        """Test complete onboarding flow."""
        # Mock all user inputs
        mock_input.side_effect = [
            "Alice",  # name
            "1",  # persona selection
            "Computer Science",  # academic field
            "Python",  # topic 1
            "AI",  # topic 2
            "",  # finish topics
            "Pass exams",  # goal 1
            "",  # finish goals
            "1,2",  # pain points
        ]

        profile = onboarding_agent.run_onboarding("test_user")

        # Verify profile was created correctly
        assert profile.user_id == "test_user"
        assert profile.name == "Alice"
        assert profile.primary_persona in OnboardingAgent.PERSONAS
        assert profile.academic_field == "Computer Science"
        assert "Python" in profile.study_topics
        assert "AI" in profile.study_topics
        assert "Pass exams" in profile.goals
        assert len(profile.traits) == 2

        # Verify profile was saved
        profile_path = temp_profiles_dir / "test_user.json"
        assert profile_path.exists()

        # Verify saved profile can be loaded
        loaded_profile = onboarding_agent.profile_store.load("test_user")
        assert loaded_profile.user_id == profile.user_id
        assert loaded_profile.name == profile.name

    @patch("builtins.input")
    def test_onboarding_keyboard_interrupt(self, mock_input, onboarding_agent):
        """Test onboarding handles keyboard interrupt."""
        mock_input.side_effect = KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            onboarding_agent.run_onboarding("test_user")

    def test_profile_store_integration(self, onboarding_agent, temp_profiles_dir):
        """Test that OnboardingAgent correctly integrates with UserProfileStore."""
        # Create a profile manually
        profile = UserProfile(
            user_id="test_integration",
            name="Test User",
            primary_persona="Richard Feynman",
            preferred_personas=["Richard Feynman"],
            study_topics=["Physics"],
            goals=["Learn quantum mechanics"],
            traits=["procrastination"],
        )

        # Save it
        onboarding_agent.profile_store.save(profile)

        # Verify it can be loaded
        loaded = onboarding_agent.profile_store.load("test_integration")
        assert loaded.user_id == "test_integration"
        assert loaded.name == "Test User"
        assert loaded.primary_persona == "Richard Feynman"


class TestOnboardingDataValidation:
    """Test data validation during onboarding."""

    @patch("builtins.input")
    def test_profile_with_minimal_data(self, mock_input, onboarding_agent):
        """Test profile creation with minimal required data."""
        mock_input.side_effect = [
            "Bob",  # name
            "1",  # persona
            "",  # skip academic field
            "",  # no topics
            "",  # no goals
            "",  # no pain points
        ]

        profile = onboarding_agent.run_onboarding("minimal_user")

        assert profile.user_id == "minimal_user"
        assert profile.name == "Bob"
        assert profile.primary_persona in OnboardingAgent.PERSONAS
        assert profile.study_topics == []
        assert profile.goals == []
        assert profile.traits == []

    def test_created_profile_is_valid_pydantic_model(self, profile_store):
        """Test that created profiles are valid Pydantic models."""
        profile = UserProfile(
            user_id="pydantic_test",
            name="Test",
            primary_persona="Steve Jobs",
            preferred_personas=["Steve Jobs"],
            study_topics=["Coding"],
            goals=["Build apps"],
            traits=["perfectionism"],
        )

        # Should not raise validation errors
        profile_store.save(profile)

        # Load and verify
        loaded = profile_store.load("pydantic_test")
        assert isinstance(loaded, UserProfile)
        assert loaded.user_id == "pydantic_test"
