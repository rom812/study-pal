"""Agent package exposing specialized study assistants."""

from .scheduler_agent import OpenAIConversationModel, SchedulerAgent
from .motivator_agent import MotivatorAgent, OpenAIMotivationModel
from .quote_store import Quote, QuoteStore
from .user_profile import UserProfile, UserProfileStore, UserProgressEvent
from .weakness_detector_agent import WeaknessDetectorAgent

try:
    from .tutor_agent import TutorAgent
    _tutor_available = True
except ImportError as e:
    TutorAgent = None  # type: ignore
    _tutor_available = False
    _tutor_import_error = str(e)

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
    "WeaknessDetectorAgent",
]

if _quote_scraper_available:
    __all__.extend(["WebSearchQuoteScraper", "PersonalizedQuoteGenerator"])
