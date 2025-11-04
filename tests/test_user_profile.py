"""Tests for user profile models used by the Motivator agent."""

from __future__ import annotations

from agents.user_profile import UserProfile, UserProfileStore, UserProgressEvent


def test_register_event_keeps_recent_entries_only(tmp_path) -> None:
    profile = UserProfile(user_id="rom", name="Rom")

    for idx in range(60):
        profile.register_event(
            UserProgressEvent(category="win", summary=f"event-{idx}")
        )

    assert len(profile.progress_log) == 50
    assert profile.progress_log[0].summary == "event-10"
    assert profile.progress_log[-1].summary == "event-59"


def test_profile_store_roundtrip(tmp_path) -> None:
    store = UserProfileStore(tmp_path)
    profile = UserProfile(
        user_id="learner",
        name="Learner",
        primary_persona="Kobe Bryant",
        study_topics=["Neural Networks"],
    )
    store.save(profile)

    loaded = store.load("learner")

    assert loaded.user_id == "learner"
    assert loaded.primary_persona == "Kobe Bryant"
    assert loaded.study_topics == ["Neural Networks"]
