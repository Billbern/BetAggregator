"""Tests for the pure scrapers: no browser required."""

from app.scraper import (
    SlipData,
    parse_betway_page,
    parse_odds,
    parse_sportybet_page,
)
from app.scraper.base import GameData

SPORTYBET_HTML = """
<div class="m-outcomes-list">
  <div class="m-bet-container">
    <div class="m-outcomes-row">
      <div class="m-outcome-right">
        <div class="m-team-cell">
          <a>
            <div>Home<!-- -->/<!-- -->Draw</div>
            <div>2.40</div>
            <div>Heart of Lions <!-- -->v<!-- --> Asante Kotoko</div>
          </a>
        </div>
      </div>
    </div>
  </div>
  <div class="m-bet-container">
    <div class="m-outcomes-row">
      <div class="m-outcome-right">
        <div class="m-team-cell">
          <a>
            <div>Over 2.5</div>
            <div>1.85</div>
            <div>Medeama <!-- -->v<!-- --> Hearts of Oak</div>
          </a>
        </div>
      </div>
    </div>
  </div>
</div>
"""

BETWAY_HTML = """
<ul>
  <li class="SelectedOutcomeForBetslip ms-divider">
    <label class="outcomeRow-title" data-translate-market="1X2"
           data-translate-set="Full Time">1</label>
    <label class="outcomeRow-Info">Real Madrid v Barcelona</label>
    <div class="betslipPriceDecimal">1.66</div>
  </li>
  <li class="SelectedOutcomeForBetslip ms-divider">
    <label class="outcomeRow-title" data-translate-market="Totals"
           data-translate-set="Full Time">Over 2.5</label>
    <label class="outcomeRow-Info">Bayern v Dortmund</label>
    <div class="betslipPriceDecimal">2.25</div>
  </li>
</ul>
"""


def test_parse_sportybet_page():
    games = parse_sportybet_page(SPORTYBET_HTML)
    assert len(games) == 2
    assert games[0] == GameData(
        match="Heart of Lions v Asante Kotoko", option="Home/Draw", odds=2.4
    )
    assert games[1].option == "Over 2.5"
    assert games[1].odds == 1.85


def test_parse_sportybet_empty():
    assert parse_sportybet_page("<html><body></body></html>") == []


def test_parse_betway_page():
    games = parse_betway_page(BETWAY_HTML)
    assert len(games) == 2
    assert games[0].match == "Real Madrid v Barcelona"
    assert games[0].option == "1"
    assert games[0].odds == 1.66
    assert games[1].odds == 2.25


def test_parse_betway_empty():
    assert parse_betway_page("<html/>") == []


def test_parse_odds():
    assert parse_odds("2.15") == 2.15
    assert parse_odds("  1,90 ") == 1.9  # comma decimal separator
    assert parse_odds("abc") == 0.0


def test_slip_data_odds_product_and_validity():
    valid = SlipData(
        code="ABC",
        games=[
            GameData(match="A v B", option="Home", odds=2.0),
            GameData(match="C v D", option="Away", odds=1.5),
        ],
    )
    assert valid.odds == 3.0
    assert valid.valid is True

    empty = SlipData(code="EMPTY", games=[])
    assert empty.valid is False

    low = SlipData(
        code="LOW",
        games=[GameData(match="A v B", option="Home", odds=0.8)],
    )
    assert low.valid is False  # odds must exceed 1


def test_slip_data_as_dict():
    data = SlipData(code="X1", games=[GameData("A v B", "Home", 2.0)])
    payload = data.as_dict()
    assert payload["code"] == "X1"
    assert payload["odds"] == 2.0
    assert payload["games"][0]["match"] == "A v B"
