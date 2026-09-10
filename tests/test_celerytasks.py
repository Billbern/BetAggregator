"""Tests for the Celery scrape pipeline (provider mocked, no browser)."""

import pytest

from app.extensions import db
from app.models import Slip, SlipCursor
from app.scraper.base import GameData, ScraperError, SlipData
from app.utils import celerytasks
from app.utils.celerytasks import run_scrape_pipeline


class FakeProvider:
    """Provider that fails for one code and returns empty for another."""

    fail_codes: set[str] = {"BC8GMS7Z"}
    empty_codes: set[str] = {"BC8GMS8A"}

    def __init__(self, country=None):
        self.country = country

    def get_slip(self, code):
        if code in self.fail_codes:
            raise ScraperError("network is a lie")
        if code in self.empty_codes:
            return SlipData(code=code, games=[])
        return SlipData(
            code=code,
            games=[GameData(match="A v B", option="Home", odds=2.0)],
        )


@pytest.fixture()
def app_ctx(app):
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def cursor(app_ctx):
    c = SlipCursor(country="ghana", code="BC8GMS7A")
    db.session.add(c)
    db.session.commit()
    return c


@pytest.fixture()
def use_fake_provider(monkeypatch):
    def _provider(country=None):
        return FakeProvider(country)

    monkeypatch.setattr(celerytasks, "available_providers", lambda: {"fake": _provider})


def codes(count):
    from app.utils.slipgenerator import generate_slips

    return generate_slips("BC8GMS7A", count)


def test_pipeline_persists_valid_and_advances_cursor(app_ctx, cursor, use_fake_provider):
    result = run_scrape_pipeline(country="ghana", n=3, provider="fake")

    stored = {s.code for s in Slip.query.all()}
    assert stored == {"BC8GMS7A", "BC8GMS7B", "BC8GMS7C"}
    assert result["saved"] == ["BC8GMS7A", "BC8GMS7B", "BC8GMS7C"]
    assert result["failed"] == []
    assert SlipCursor.query.filter_by(country="ghana").one().code == codes(3)[-1]


def test_pipeline_deduplicates_existing_slips(app_ctx, cursor, use_fake_provider):
    db.session.add(Slip(code="BC8GMS7B", odds=2.0))
    db.session.commit()

    result = run_scrape_pipeline(country="ghana", n=3, provider="fake")
    assert Slip.query.count() == 3  # existing code not re-inserted
    assert result["saved"] == ["BC8GMS7A", "BC8GMS7C"]
    # cursor still advances past every attempted code
    assert SlipCursor.query.filter_by(country="ghana").one().code == codes(3)[-1]


def test_pipeline_counts_failures_and_invalids(app_ctx, cursor, use_fake_provider, monkeypatch):
    monkeypatch.setattr(FakeProvider, "fail_codes", {"BC8GMS7B"})
    monkeypatch.setattr(FakeProvider, "empty_codes", {"BC8GMS7C"})

    result = run_scrape_pipeline(country="ghana", n=3, provider="fake")
    assert result["attempted"] == 3
    assert result["failed"] == ["BC8GMS7B"]
    assert result["skipped"] == ["BC8GMS7C"]
    assert result["saved"] == ["BC8GMS7A"]
    stored = {s.code for s in Slip.query.all()}
    assert stored == {"BC8GMS7A"}


def test_pipeline_missing_cursor(app_ctx):
    with pytest.raises(ValueError):
        run_scrape_pipeline(country="zzz", n=2, provider="fake")


def test_pipeline_unknown_provider(app_ctx, cursor):
    with pytest.raises(ValueError):
        run_scrape_pipeline(country="ghana", n=2, provider="nope")
