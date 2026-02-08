"""European competition scrapers."""

from .epcr import EPCRChampionsCupScraper, EPCRChallengeCupScraper
from .top14 import Top14Scraper
from .rugbyviz import GallagherPremiershipScraper, UnitedRugbyChampionshipScraper

__all__ = [
    "EPCRChampionsCupScraper",
    "EPCRChallengeCupScraper",
    "Top14Scraper",
    "GallagherPremiershipScraper",
    "UnitedRugbyChampionshipScraper",
]
