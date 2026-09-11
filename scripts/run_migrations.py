#!/usr/bin/env python3
"""Run Alembic migrations under a cross-backend lock.

Every app container (web, worker, beat) runs this on startup. Without a lock,
concurrent ``flask db upgrade`` calls race on the schema:

* PostgreSQL → ``duplicate key value violates unique constraint
  pg_type_typname_nsp_index`` (the original beat crash), and
* SQLite (local dev) → ``table country already exists``.

To serialize them we use the strongest lock the backend provides:

* PostgreSQL: a session-level ``pg_advisory_lock`` (survives process
  restarts, automatically released on disconnect).
* Anything else (SQLite dev, etc.): an exclusive ``fcntl.flock`` on a
  local lockfile (auto-released on process exit).

``flask db upgrade`` is idempotent, so whichever process wins the race
migrates and the losers run a no-op upgrade afterwards.
"""

from __future__ import annotations

import fcntl
import logging
import os
import subprocess
import sys
import time
from urllib.parse import urlparse

logger = logging.getLogger("run_migrations")
logging.basicConfig(level=logging.INFO, format="%(message)s")

# Arbitrary app-scoped key; must match across all replicas so they share it.
MIGRATION_LOCK_KEY = 727_000_001
LOCK_TIMEOUT_S = 300
POLL_INTERVAL_S = 2


def run_flask_upgrade() -> None:
    subprocess.run(
        [sys.executable, "-m", "flask", "--app", "wsgi", "db", "upgrade"],
        check=True,
    )


def _postgres_params(url: str) -> dict:
    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "user": parsed.username,
        "password": parsed.password,
        "dbname": parsed.path.lstrip("/") or "postgres",
    }


def _run_with_advisory_lock(params: dict) -> None:
    import psycopg

    conn = psycopg.connect(**params, autocommit=True)
    acquired = False
    try:
        deadline = time.monotonic() + LOCK_TIMEOUT_S
        while time.monotonic() < deadline:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_try_advisory_lock(%s)", (MIGRATION_LOCK_KEY,))
                acquired = cur.fetchone()[0]
            if acquired:
                break
            logger.info("... waiting for migrations lock held by another service")
            time.sleep(POLL_INTERVAL_S)

        if not acquired:
            raise TimeoutError("timed out waiting for migrations advisory lock")

        run_flask_upgrade()
    finally:
        if acquired:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_unlock(%s)", (MIGRATION_LOCK_KEY,))
        conn.close()


def run_flask_upgrade_locked() -> None:
    """Direct (non-Postgres) upgrade protected by an exclusive file lock."""
    lock_path = os.environ.get(
        "MIGRATION_LOCKFILE", os.path.join("/tmp", "betaggregator-migrate.lock")
    )
    with open(lock_path, "w") as lock_file:
        deadline = time.monotonic() + LOCK_TIMEOUT_S
        while True:
            try:
                fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("timed out waiting for migration lockfile") from None
                logger.info("... waiting for migrations lock held by another service")
                time.sleep(POLL_INTERVAL_S)
        try:
            run_flask_upgrade()
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def main() -> int:
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("postgresql"):
        _run_with_advisory_lock(_postgres_params(url.split("+", 1)[-1]))
    else:
        run_flask_upgrade_locked()
    return 0


if __name__ == "__main__":
    sys.exit(main())
