"""Scraping foundation: data types, configuration, and an exception type.

The drivers are wrapped in a context manager so each scrape gets a *fresh*
Firefox instance. The original code quit the driver inside the scrape method,
so a second call on the same scraper crashed with ``AttributeError``.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class ScraperError(RuntimeError):
    """Raised when a scrape fails after retries / the page is unusable."""


@dataclass(frozen=True)
class GameData:
    """One market/selection returned for a slip code."""

    match: str
    option: str
    odds: float

    def as_dict(self) -> dict:
        return {"match": self.match, "option": self.option, "odds": self.odds}


@dataclass(frozen=True)
class SlipData:
    """The fully scraped contents of a single slip."""

    code: str
    games: list[GameData] = field(default_factory=list)

    @property
    def odds(self) -> float:
        product = 1.0
        for game in self.games:
            if game.odds > 0:
                product *= game.odds
        return round(product, 2)

    @property
    def valid(self) -> bool:
        """A slip is worth persisting if it has games and odds above 1."""
        return len(self.games) > 0 and self.odds > 1

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "games": [g.as_dict() for g in self.games],
            "odds": self.odds,
        }


@dataclass(frozen=True)
class ScraperConfig:
    """Tunables for a provider; defaults match the original bookmaker flow."""

    base_url: str
    geckodriver_path: str = "geckodriver"
    log_path: str | None = None
    page_load_timeout_s: float = 30.0
    wait_timeout_s: float = 60.0
    headless: bool = True


def _build_driver(config: ScraperConfig):
    """Create a headless Firefox driver with sensible defaults."""
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.firefox.service import Service

    options = Options()
    options.set_preference("permissions.default.image", 2)
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--incognito")
    if config.headless:
        options.add_argument("--headless")

    kwargs = {"options": options}
    if config.log_path:
        kwargs["service_log_path"] = config.log_path
    driver = webdriver.Firefox(service=Service(executable_path=config.geckodriver_path), **kwargs)
    driver.set_page_load_timeout(config.page_load_timeout_s)
    return driver


class ManagedDriver:
    """Context manager that owns a driver instance for one scrape."""

    def __init__(self, config: ScraperConfig):
        self._config = config
        self.driver = None

    def __enter__(self):
        self.driver = _build_driver(self._config)
        return self.driver

    def __exit__(self, exc_type, exc, tb):
        if self.driver is not None:
            try:
                self.driver.quit()
            finally:
                self.driver = None
        return False


def parse_odds(text: str) -> float:
    """Parse a price string like ``2.15`` (or ``2,15``) into a float."""
    try:
        return float(text.strip().replace(",", "."))
    except ValueError:
        return 0.0
