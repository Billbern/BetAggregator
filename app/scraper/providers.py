"""Bookmaker providers.

Each provider knows how to (a) navigate to its site and submit a slip code,
and (b) parse the resulting page into :class:`GameData`. Parsing lives in
pure functions so it can be unit-tested against saved HTML fixtures without
a browser (see ``tests/fixtures``).
"""

from __future__ import annotations

import logging

from bs4 import BeautifulSoup

from app.scraper.base import (
    GameData,
    ManagedDriver,
    ScraperConfig,
    ScraperError,
    SlipData,
    parse_odds,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pure parsers (unit-testable without a browser)
# ---------------------------------------------------------------------------


def parse_sportybet_page(html: str) -> list[GameData]:
    """Extract games from a sportybet (mobile) slip page."""
    soup = BeautifulSoup(html, "lxml")
    container = soup.find("div", attrs={"class": "m-outcomes-list"})
    if container is None:
        return []

    games: list[GameData] = []
    for block in container.find_all("div", attrs={"class": "m-bet-container"}):
        row = block.find("div", attrs={"class": "m-outcomes-row"})
        if row is None:
            continue
        cell = row.find("div", attrs={"class": "m-team-cell"})
        if cell is None or cell.find("a") is None:
            continue
        values = [div.text for div in cell.find("a").find_all("div")]
        values = [v.strip() for v in values if v and v.strip()]
        # sportybet paints cells in the order: option, odds, match
        if len(values) >= 3:
            games.append(
                GameData(
                    match=values[-1],
                    option=values[0],
                    odds=parse_odds(values[1]),
                )
            )
    return games


def parse_betway_page(html: str) -> list[GameData]:
    """Extract games from a betway betslip page."""
    soup = BeautifulSoup(html, "lxml")
    games: list[GameData] = []
    for item in soup.find_all("li", attrs={"class": "SelectedOutcomeForBetslip ms-divider"}):
        info = item.find("label", {"class": "outcomeRow-Info"})
        title = item.find("label", {"class": "outcomeRow-title"})
        price = item.find("div", {"class": "betslipPriceDecimal"})
        if info is None or title is None or price is None:
            continue
        match = info.get_text(" ", strip=True)
        option = title.get_text(" ", strip=True)
        games.append(GameData(match=match, option=option, odds=parse_odds(price.text)))
    return games


# ---------------------------------------------------------------------------
# Browser-driven providers
# ---------------------------------------------------------------------------


class SportyBetProvider:
    """Slip lookup against sportybet.com mobile (multi-country)."""

    COUNTRY_DATA_IDS = {
        "kenya": "1",
        "nigeria": "2",
        "tanzania": "3",
        "uganda": "4",
        "zambia": "5",
    }

    def __init__(
        self,
        config: ScraperConfig | None = None,
        country: str = "ghana",
    ):
        self.country = country
        self.config = config or ScraperConfig(base_url="https://www.sportybet.com/gh/m")

    def get_slip(self, code: str) -> SlipData:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        with ManagedDriver(self.config) as driver:
            driver.get(self.config.base_url)
            try:
                self._dismiss_floaters(driver)
                self._select_country(driver)
                self._submit_code(driver, code)
                WebDriverWait(driver, self.config.wait_timeout_s).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".m-betslips-show .m-betslips-outcomes")
                    )
                )
                return SlipData(
                    code=code,
                    games=parse_sportybet_page(driver.page_source),
                )
            except Exception as exc:  # noqa: BLE001 - normalize driver errors
                raise ScraperError(f"failed to scrape {code!r} from sportybet") from exc

    @staticmethod
    def _dismiss_floaters(driver) -> None:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        try:
            floater = driver.find_element(By.CSS_SELECTOR, ".es-dialog-wrap .layout")
            WebDriverWait(driver, 5).until(EC.visibility_of_element_located(floater))
            if floater.is_displayed():
                driver.execute_script("document.querySelector('.layout').style.zIndex = '1200'")
                floater.click()
        except Exception:  # noqa: BLE001 - layout drift should not abort
            logger.warning("sportybet floater not dismissed", exc_info=True)

    def _select_country(self, driver) -> None:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        data_id = self.COUNTRY_DATA_IDS.get(self.country)
        if not data_id:
            return  # ghana is the default site
        wait = WebDriverWait(driver, self.config.wait_timeout_s)
        wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".country-main > .af-select-title"))
        ).click()
        wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, f".af-select-list > span[data-id='{data_id}']")
            )
        ).click()

    def _submit_code(self, driver, code: str) -> None:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        wait = WebDriverWait(driver, self.config.wait_timeout_s)
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "betslip-float-wrapper"))).click()
        elem = driver.find_element(by=By.CLASS_NAME, value="m-input-wap")
        elem.send_keys(code)
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "share-code-btn"))).click()


class BetwayProvider:
    """Slip lookup against betway.com.gh."""

    def __init__(self, config: ScraperConfig | None = None):
        self.config = config or ScraperConfig(
            base_url="https://www.betway.com.gh/",
            geckodriver_path="app/scraper/geckodriver",
        )

    def get_slip(self, code: str) -> SlipData:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        with ManagedDriver(self.config) as driver:
            driver.get(self.config.base_url)
            try:
                try:
                    WebDriverWait(driver, self.config.wait_timeout_s).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#helphero-dom > iframe"))
                    )
                    driver.execute_script(
                        "document.querySelector('#helphero-dom > iframe').style.display = 'none';"
                    )
                except Exception:  # noqa: BLE001 - iframe is optional
                    logger.warning("betway iframe not hidden", exc_info=True)

                try:
                    opener = driver.find_element(By.CSS_SELECTOR, "#headerBtnBetslip")
                    if opener.is_displayed():
                        opener.click()
                except Exception:  # noqa: BLE001 - betslip may already be open
                    logger.warning("betway betslip opener not clicked", exc_info=True)

                WebDriverWait(driver, self.config.wait_timeout_s).until(
                    EC.presence_of_element_located((By.ID, "mtSearch"))
                )
                driver.find_element(By.ID, "mtSearch").send_keys(code)
                driver.find_element(By.ID, "searchIconBetslip").click()
                WebDriverWait(driver, self.config.wait_timeout_s).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#betslip-list > li"))
                )
                return SlipData(
                    code=code,
                    games=parse_betway_page(driver.page_source),
                )
            except Exception as exc:  # noqa: BLE001 - normalize driver errors
                raise ScraperError(f"failed to scrape {code!r} from betway") from exc


def available_providers() -> dict[str, type]:
    """Registry of provider classes keyed by name."""
    return {"sportybet": SportyBetProvider, "betway": BetwayProvider}
