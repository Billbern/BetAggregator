# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        firefox-esr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/betaggregator

# Install Python deps (cached layer).
COPY pyproject.toml requirements.txt README.md ./
COPY app ./app
RUN pip install -e .

# geckodriver is fetched at build time (never committed). Pin a known-good
# version and verify its checksum to keep the supply chain clean.
ARG GECKODRIVER_VERSION=v0.34.0
ARG GECKODRIVER_SHA256=9a7373bd72793b0f1e0a29a3316d0e519a566230c2903685988ac85ffe42ff34
RUN curl -fsSLo /tmp/geckodriver.tar.gz \
        "https://github.com/mozilla/geckodriver/releases/download/${GECKODRIVER_VERSION}/geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz" \
    && echo "${GECKODRIVER_SHA256}  /tmp/geckodriver.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin \
    && rm /tmp/geckodriver.tar.gz \
    && geckodriver --version | head -1

RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /srv/betaggregator/logs \
    && chown -R appuser:appuser /srv/betaggregator
USER appuser

COPY --chown=appuser:appuser . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "-k", "gevent", "--worker-connections", "1000", "wsgi:app"]