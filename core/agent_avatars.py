"""Agent avatar configuration for Study Pal."""

# Avatar emojis for each agent type
AGENT_AVATARS = {
    "tutor": "📚",  # Book for teaching/tutoring
    "scheduler": "📅",  # Calendar for scheduling
    "analyzer": "🔍",  # Magnifying glass for analysis
    "motivator": "💪",  # Flexed bicep for motivation
    "router": "🧭",  # Compass for routing/navigation
    "user": "👤",  # Person silhouette for user
    "system": "🤖",  # Robot for system messages
}


def get_agent_avatar(agent_name: str) -> str:
    """
    Get the emoji avatar for an agent.

    Args:
        agent_name: Name of the agent (tutor, scheduler, analyzer, motivator, router)

    Returns:
        Emoji string for the agent avatar
    """
    return AGENT_AVATARS.get(agent_name.lower(), "🤖")


def get_user_avatar() -> str:
    """Get the emoji avatar for the user."""
    return AGENT_AVATARS["user"]
