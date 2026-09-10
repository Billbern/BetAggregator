"""Celery tasks: the slip-scraping pipeline.

This replaces the original blocking ``generator()`` worker function (which
polled job results over RQ) with a single skippable task that:

1. reads the per-country cursor,
2. generates the next ``n`` codes,
3. scrapes each code with the configured provider,
4. persists valid slips (games > 0, combined odds > 1) and
5. advances the cursor to the last generated code.
"""

from __future__ import annotations

import logging

from app.celery_app import celery
from app.extensions import db
from app.models import Game, Slip, SlipCursor
from app.scraper import ScraperError, available_providers
from app.utils.slipgenerator import generate_slips

logger = logging.getLogger(__name__)


def run_scrape_pipeline(
    country: str,
    n: int = 10,
    provider: str = "sportybet",
) -> dict:
    """Generate, scrape and persist ``n`` slips for ``country``.

    This is the testable core; the Celery task is a thin wrapper so tests can
    call it without entering the worker app context.
    """
    provider_cls = available_providers().get(provider)
    if provider_cls is None:
        raise ValueError(f"unknown provider {provider!r}")

    cursor = SlipCursor.query.filter_by(country=country).first()
    if cursor is None:
        raise ValueError(f"no cursor for country {country!r}; run `flask seed`")

    codes = generate_slips(cursor.code, n)
    scraper = provider_cls(country=country)

    saved: list[str] = []
    skipped: list[str] = []
    failed: list[str] = []
    for code in codes:
        outcome = _persist_code(code, scraper)
        if outcome == "saved":
            saved.append(code)
        elif outcome == "skipped":
            skipped.append(code)
        else:
            failed.append(code)

    cursor.code = codes[-1]
    db.session.commit()

    logger.info(
        "pipeline done country=%s codes=%d saved=%d skipped=%d failed=%d",
        country,
        len(codes),
        len(saved),
        len(skipped),
        len(failed),
    )
    return {
        "country": country,
        "attempted": len(codes),
        "saved": saved,
        "skipped": skipped,
        "failed": failed,
        "cursor": cursor.code,
    }


def _persist_code(code: str, scraper) -> str:
    """Scrape one code and optionally persist it.

    Returns ``"saved"`` when a new slip was stored, ``"skipped"`` when the
    slip was scraped but did not qualify, and ``"failed"`` when the code was
    already stored or scraping itself failed.
    """
    if Slip.query.filter_by(code=code).first() is not None:
        return "failed"  # already persisted (dedupe)

    try:
        result = scraper.get_slip(code)
    except ScraperError:
        logger.warning("scrape failed for %s", code, exc_info=True)
        return "failed"

    if not result.valid:
        logger.info(
            "skipped invalid slip %s (odds=%.2f, games=%d)",
            code,
            result.odds,
            len(result.games),
        )
        return "skipped"

    slip = Slip(code=result.code, odds=result.odds)
    db.session.add(slip)
    db.session.flush()
    for game in result.games:
        db.session.add(
            Game(
                match=game.match,
                option=game.option,
                odds=game.odds,
                slip_id=slip.id,
            )
        )
    return "saved"


@celery.task(name="app.utils.celerytasks.scrape_slip_codes")
def scrape_slip_codes(
    country: str,
    n: int = 10,
    provider: str = "sportybet",
) -> dict:
    """Celery entry point for :func:`run_scrape_pipeline`."""
    return run_scrape_pipeline(country, n, provider)
    return "saved"
