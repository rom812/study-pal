"""Agent package exposing specialized study assistants."""

from .scheduler_agent import OpenAIConversationModel, SchedulerAgent
from .motivator_agent import MotivatorAgent, OpenAIMotivationModel
from .tutor_agent import TutorAgent
from .quote_store import Quote, QuoteStore
from .user_profile import UserProfile, UserProfileStore, UserProgressEvent

try:
    from .quote_scraper import WebSearchQuoteScraper, PersonalizedQuoteGenerator
    _quote_scraper_available = True
except ImportError:
    _quote_scraper_available = False

__all__ = [
    "SchedulerAgent",
    "OpenAIConversationModel",
    "MotivatorAgent",
    "OpenAIMotivationModel",
    "Quote",
    "QuoteStore",
    "UserProfile",
    "UserProfileStore",
    "UserProgressEvent",
    "TutorAgent",
]

if _quote_scraper_available:
    __all__.extend(["WebSearchQuoteScraper", "PersonalizedQuoteGenerator"])
