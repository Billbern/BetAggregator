# BetAggregator

Generates sequential betting-slip codes, scrapes bookmaker sites to resolve
their contents, and stores valid slips for real-time review.

This is the modern rebuild of the original `bet-slip-generator` product:
same multi-country flow (Ghana/Kenya/Nigeria/Tanzania/Uganda/Zambia) and the
per-country slip-code cursor, rebuilt on an application-factory Flask app,
SQLAlchemy 2, Alembic migrations, and a Celery worker pipeline.

## Features

- **Per-country code cursor** — generates the next slip codes in sequence
  (`1-9`, `A-Z` skipping `0/I/O`; `AZ → B1`, `ZZ → 111`), carried in the
  `slip_cursor` table.
- **Multi-provider scrapers** — `sportybet` (all countries) and `betway`
  (Ghana) behind a shared interface, with browser-free parsers.
- **Scrape → persist pipeline** — a Celery task generates `n` codes, scrapes
  them, keeps slips whose combined odds are `> 1`, deduplicates by code, and
  advances the cursor.
- **Clean schema** — slips/games for what scrapers return, plus the richer
  normalized sport graph (team/league/country/match/bet) for future features.

## Stack

Flask 3 · Flask-SQLAlchemy 3 · Flask-Migrate / Alembic · Flask-SocketIO ·
Celery 5 · Redis · PostgreSQL (psycopg) · Selenium/BeautifulSoup ·
ruff + pytest.

## Quickstart (local)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env            # edit values as needed
flask --app wsgi db upgrade     # apply migrations
flask --app wsgi seed           # seed the per-country cursors
flask --app wsgi run            # or: python main.py (dev server w/ live dashboard)
```

Run the pipeline without a broker (calls the pipeline directly):

```bash
flask --app wsgi shell
>>> from app.utils.celerytasks import run_scrape_pipeline
>>> run_scrape_pipeline(country="ghana", n=5, provider="sportybet")
```

### Celery worker

```bash
celery -A app.celery_app.celery worker --loglevel=info
```

## Testing & linting

```bash
pytest                 # 30+ tests (models, generators, parsers, pipeline)
ruff check .           # lint
ruff format --check .  # formatting
```

## Configuration

All configuration is environment-driven (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `APP_ENV` | `development` | selects config class (dev/test/staging/prod) |
| `SECRET_KEY` | dev placeholder | Flask signing secret — set in prod |
| `DATABASE_URL` | sqlite dev db | SQLAlchemy connection URI |
| `CELERY_BROKER_URL` | redis://localhost:6379/0 | Celery broker |
| `CELERY_BACKEND_URL` | redis://localhost:6379/1 | Celery results backend |
| `LOG_LEVEL` | `INFO` | logging level |
| `SOCKETIO_ASYNC_MODE` | `threading` | `threading` locally, `gevent` in prod |

## Project layout

```
app/
  __init__.py       application factory (create_app)
  extensions.py     db / migrate / socketio instances
  cli.py            flask seed command
  config/           env-driven config classes + celery factory
  models/           slip, game, slip_cursor, bet, match, team, league, ...
  scraper/          base types + sportybet / betway providers
  routes.py         / and /health HTTP routes
  utils/            slip generator, serializers, celery tasks
migrations/         Alembic migrations (baseline: a86132cf9a85)
tests/              pytest suite (conftest + unit/integration tests)
```

## Roadmap (in progress)

- [x] Application factory, env config, container-ready layout
- [x] Slug-generator + scraping + Celery pipeline (tests)
- [x] Baseline schema + seed command
- [x] Docker Compose (db/redis/web/worker) + Dockerfile (geckodriver baked in)
- [x] Socket.IO dashboard (real-time slip list + generate button)
- [ ] CI (GitHub Actions)

## License / notice

Personal project. Scraping third-party bookmaker sites may violate their
Terms of Service; use at your own risk and respect site rate limits.
