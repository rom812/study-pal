"""Stub tests for MotivatorAgent."""

from agents.motivator_agent import MotivationMessage, MotivatorAgent


class DummyFetcher:
    def fetch(self, persona: str) -> dict:
        return {"text": f"Keep going, {persona}!", "source": "dummy"}


def test_craft_message_returns_valid_model():
    agent = MotivatorAgent(fetcher=DummyFetcher())

    message = agent.craft_message(user_id="learner", persona="Kobe Bryant")

    assert isinstance(message, MotivationMessage)
    assert message.persona_style == "Kobe Bryant"
    assert "Kobe" in message.text
