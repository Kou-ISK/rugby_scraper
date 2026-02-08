"""Domestic league scrapers."""

from .league_one_divisions import LeagueOneDivisionsScraper
from .super_rugby import SuperRugbyPacificScraper

__all__ = [
    "LeagueOneDivisionsScraper",
    "SuperRugbyPacificScraper",
]
