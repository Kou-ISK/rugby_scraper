"""International competition scrapers."""

from .six_nations import SixNationsScraper, SixNationsWomensScraper, SixNationsU20Scraper
from .rugby_championship import RugbyChampionshipScraper
from .autumn_nations import AutumnNationsSeriesScraper
from .world_rugby import WorldRugbyInternationalsScraper

__all__ = [
    "SixNationsScraper",
    "SixNationsWomensScraper",
    "SixNationsU20Scraper",
    "RugbyChampionshipScraper",
    "AutumnNationsSeriesScraper",
    "WorldRugbyInternationalsScraper",
]
