#!/bin/sh
# Entrypoint for the betaggregator app image.
# Usage:  entrypoint <web|worker|beat> [extra args...]
set -e

SERVICE="${1:-web}"
shift || true

echo "==> entrypoint: waiting for database"
python - <<'PY'
import os, socket, sys, time

host, port = "localhost", 5432
try:
    url = os.environ.get("DATABASE_URL", "")
    if "+" in url:
        url = url.split("+", 1)[1]
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.hostname:
        host, port = parsed.hostname, parsed.port or 5432
except Exception as exc:  # pragma: no cover - defensive
    print("db host parse failed:", exc)

for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        time.sleep(2)
else:
    print("database not reachable; continuing anyway")
    sys.exit(0)
PY

echo "==> entrypoint: applying migrations (advisory-locked)"
python scripts/run_migrations.py

case "$SERVICE" in
  web)
    echo "==> starting web (gunicorn+gevent)"
    exec gunicorn --bind 0.0.0.0:5000 \
        -k gevent --worker-connections 1000 \
        --workers "${WEB_WORKERS:-2}" \
        "$@";;
  worker)
    echo "==> starting celery worker"
    exec celery -A app.celery_app.celery worker \
        --loglevel="${LOG_LEVEL:-info}" "$@";;
  beat)
    echo "==> starting celery beat"
    exec celery -A app.celery_app.celery beat \
        --loglevel="${LOG_LEVEL:-info}" "$@";;
  *)
    echo "Unknown service: $SERVICE (expected web|worker|beat)" >&2
    exit 2;;
esac