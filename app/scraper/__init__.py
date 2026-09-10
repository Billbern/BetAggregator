"""Scraping package.

Public surface: provider registry + the two providers (sportybet, betway).
"""

from app.scraper.base import (
    GameData,
    ManagedDriver,
    ScraperConfig,
    ScraperError,
    SlipData,
    parse_odds,
)
from app.scraper.providers import (
    BetwayProvider,
    SportyBetProvider,
    available_providers,
    parse_betway_page,
    parse_sportybet_page,
)

__all__ = [
    "BetwayProvider",
    "GameData",
    "ManagedDriver",
    "ScraperConfig",
    "ScraperError",
    "SlipData",
    "SportyBetProvider",
    "available_providers",
    "parse_betway_page",
    "parse_odds",
    "parse_sportybet_page",
]
