from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Game, Match, Slip, SlipCursor, Team


@pytest.fixture()
def app_ctx(app):
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


def make_slip(code="BC8GMS6X", odds=4.2, games=None):
    slip = Slip(code=code, odds=odds)
    db.session.add(slip)
    db.session.flush()
    for g in games or []:
        db.session.add(
            Game(
                match=g["match"],
                option=g["option"],
                odds=g["odds"],
                slip_id=slip.id,
            )
        )
    return slip


@pytest.mark.usefixtures("app_ctx")
def test_slip_as_display_shape():
    slip = make_slip()
    db.session.commit()
    display = slip.as_display()
    assert display["code"] == "BC8GMS6X"
    assert display["odds"] == 4.2
    assert display["games"] == 0
    assert display["expired"] is False
    # Datetimes are ISO strings (JSON-safe for Socket.IO transport)
    assert isinstance(display["created_at"], str)
    assert display["created_at"].endswith("Z")


@pytest.mark.usefixtures("app_ctx")
def test_slip_as_dict_serializes_games_and_dates():
    slip = make_slip(games=[{"match": "Team A vs Team B", "option": "Home", "odds": 2.1}])
    slip.created_at = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
    db.session.commit()

    payload = slip.as_dict()
    assert payload["code"] == "BC8GMS6X"
    assert payload["created_at"].endswith("Z")
    assert len(payload["games"]) == 1
    assert payload["games"][0]["match"] == "Team A vs Team B"
    assert payload["games"][0]["odds"] == 2.1


@pytest.mark.usefixtures("app_ctx")
def test_game_as_dict():
    slip = make_slip(games=[{"match": "A vs B", "option": "Away", "odds": 3.0}])
    db.session.commit()
    game = slip.games[0]
    data = game.as_dict()
    assert data["option"] == "Away"
    assert data["slip_id"] == slip.id


@pytest.mark.usefixtures("app_ctx")
def test_slip_code_unique():
    make_slip("SAME")
    db.session.commit()
    duplicate = Slip(code="SAME", odds=1.0)
    db.session.add(duplicate)
    with pytest.raises(IntegrityError):
        db.session.flush()


@pytest.mark.usefixtures("app_ctx")
def test_slip_cursor_country_unique():
    db.session.add(SlipCursor(country="ghana", code="AAA"))
    db.session.commit()
    db.session.add(SlipCursor(country="ghana", code="BBB"))
    with pytest.raises(IntegrityError):
        db.session.commit()


@pytest.mark.usefixtures("app_ctx")
def test_team_match_relationship_configured():
    home = Team(name="Hearts")
    away = Team(name="Oak")
    db.session.add_all([home, away])
    db.session.flush()
    match = Match(home_id=home.id, away_id=away.id)
    db.session.add(match)
    db.session.commit()

    assert home.home_matches == [match]
    assert away.away_matches == [match]
    assert match.home_team is home
    assert match.away_team is away


def test_index(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Slip Generator" in resp.data
    assert b"socket.io.js" in resp.data  # dashboard assets wired in


def test_static_assets(client):
    for path in (
        "/static/js/socket.io.js",
        "/static/js/moment.min.js",
        "/static/js/index.js",
        "/static/css/style.css",
    ):
        resp = client.get(path)
        assert resp.status_code == 200, f"missing static asset {path}"


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["status"] == "ok"
