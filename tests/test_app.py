import pytest

from app import create_app


@pytest.fixture()
def app():
    app = create_app("testing")
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_index(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"BetAggregator" in resp.data


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["status"] == "ok"
