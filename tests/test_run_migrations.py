"""Tests for the cross-backend locked migration runner.

The runner needs a real Postgres for a live advisory lock, so we verify its
logic (lock/unlock pairing, flock on the SQLite path, subprocess invocation)
with a fake psycopg connection and monkeypatched subprocess calls.
"""

import importlib.util
import sys

import pytest

_SCHEMA = "scripts/run_migrations.py"
_spec = importlib.util.spec_from_file_location("run_migrations", _SCHEMA)
rm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rm)


class FakeConn:
    """A fake psycopg connection with PG advisory-lock semantics."""

    def __init__(self):
        self.statements = []
        self.closed = False

    def connect(self, **kwargs):
        self.kwargs = kwargs
        return self

    def cursor(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.statements.append((sql, params))
        self._result = (True,)
        return self

    def fetchone(self):
        return self._result

    def close(self):
        self.closed = True


@pytest.fixture()
def fake_psycopg(monkeypatch):
    fake = FakeConn()
    fake_module = type(sys)("fake_psycopg")
    fake_module.connect = fake.connect
    monkeypatch.setitem(sys.modules, "psycopg", fake_module)
    return fake


def _fake_run(monkeypatch):
    calls = []
    monkeypatch.setattr(rm, "run_flask_upgrade", lambda: calls.append("upgrade"))
    return calls


def test_postgres_params_parses_url():
    params = rm._postgres_params("postgresql+psycopg://user:pass@dbhost:5544/betagg")
    assert params == {
        "host": "dbhost",
        "port": 5544,
        "user": "user",
        "password": "pass",
        "dbname": "betagg",
    }


def test_postgres_params_defaults():
    params = rm._postgres_params("postgresql://localhost/betagg")
    assert params["host"] == "localhost"
    assert params["port"] == 5432
    assert params["dbname"] == "betagg"


def test_advisory_lock_pair_upgrade_called(fake_psycopg, monkeypatch):
    calls = _fake_run(monkeypatch)

    rm._run_with_advisory_lock({"host": "db"})

    assert calls == ["upgrade"]
    stmts = [s for s, _ in fake_psycopg.statements]
    assert any("pg_try_advisory_lock" in s for s in stmts)
    assert any("pg_advisory_unlock" in s for s in stmts)
    assert fake_psycopg.closed is True


def test_runner_sqlite_uses_file_lock(monkeypatch, tmp_path):
    db = tmp_path / "dev.db"
    lock = tmp_path / "migrate.lock"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db}")
    monkeypatch.setenv("MIGRATION_LOCKFILE", str(lock))
    called = []
    monkeypatch.setattr(rm, "run_flask_upgrade", lambda: called.append("upgrade"))

    assert rm.main() == 0
    assert called == ["upgrade"]
    assert lock.exists()


def test_runner_non_postgres_falls_through(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "mysql://user@db/agg")
    monkeypatch.setenv("MIGRATION_LOCKFILE", str(tmp_path / "m.lock"))
    called = []
    monkeypatch.setattr(rm, "run_flask_upgrade", lambda: called.append("upgrade"))

    assert rm.main() == 0
    assert called == ["upgrade"]
