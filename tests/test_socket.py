"""Tests for the Socket.IO helpers (DB-backed scaffolding)."""

import pytest

from app.extensions import db
from app.models import Slip
from app.socket import _fetch_slip, _fetch_slips


@pytest.fixture()
def app_ctx(app):
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.mark.usefixtures("app_ctx")
def test_fetch_slips_display_contract():
    db.session.add(Slip(code="ABC", odds=3.0))
    db.session.commit()

    rows = _fetch_slips()
    assert len(rows) == 1
    assert rows[0]["code"] == "ABC"
    assert rows[0]["odds"] == 3.0
    assert rows[0]["games"] == 0  # compact display uses game count
    assert "created_at" in rows[0]


@pytest.mark.usefixtures("app_ctx")
def test_fetch_slip_detail():
    slip = Slip(code="ABC", odds=2.5)
    db.session.add(slip)
    db.session.commit()

    detail = _fetch_slip("ABC")
    assert detail is not None
    assert detail["code"] == "ABC"
    assert "games" in detail  # full payload includes the games list

    assert _fetch_slip("NOPE") is None


def test_socket_connect_sends_slips(app_ctx):
    from app.extensions import socketio

    # The fixture yields the Flask app; use it to spin up a socket client.
    test_app = app_ctx
    db.session.add(Slip(code="JOIN1", odds=1.5))
    db.session.commit()

    client = socketio.test_client(test_app)
    try:
        assert client.is_connected()
        received = client.get_received()
        assert any(e["name"] == "data" for e in received)
        data = next(e for e in received if e["name"] == "data")["args"][0]
        assert data["activity"] == "connection"
        assert data["data"][0]["code"] == "JOIN1"
    finally:
        client.disconnect()


def test_socket_initslip_persists_and_returns(app_ctx):
    from app.extensions import socketio

    client = socketio.test_client(app_ctx)
    try:
        client.emit("initslip", {"code": "MANUAL1", "country": "ghana"})
        received = client.get_received()
        data_events = [e for e in received if e["name"] == "data"]
        assert data_events, f"expected a data event, got {received}"
        assert data_events[-1]["args"][0]["data"][0]["code"] == "MANUAL1"
    finally:
        client.disconnect()
