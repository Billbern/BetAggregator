"""Socket.IO event handlers for the live dashboard.

Replaces the old repo's blocking handlers (which polled an RQ job inside the
event loop and froze the UI). The new flow is:

1. client emits ``generate {country}``
2. we enqueue ``scrape_slip_codes`` on Celery…
3. …and push an immediate ``data`` event letting the UI show "generating"
4. a background thread waits on the Celery result and emits ``data`` again
   when the run completes (or ``error`` on failure)

No job-polling happens inside the request/event loop.
"""

from __future__ import annotations

import threading
from contextlib import suppress
from datetime import UTC, datetime

from flask_socketio import emit

from app.celery_app import celery
from app.extensions import db, socketio
from app.models import Slip
from app.utils.serializers import to_iso


def _fetch_slips(limit: int = 100) -> list[dict]:
    slips = Slip.query.order_by(Slip.created_at.desc()).limit(limit).all()
    return [s.as_display() for s in slips]


def _fetch_slip(code: str) -> dict | None:
    slip = Slip.query.filter_by(code=code).first()
    return slip.as_dict() if slip else None


def _emit_latest(activity: str) -> None:
    emit("data", {"activity": activity, "data": _fetch_slips()})


@socketio.on("connect")
def handle_connect(_auth=None):
    emit("data", {"activity": "connection", "data": _fetch_slips()})


@socketio.on("fetch")
def handle_fetch(data):
    if data.get("get"):
        _emit_latest("fetching")


@socketio.on("initslip")
def handle_init_slip(data):
    """Persist a manual slip (the old ``Zero`` flow, now on Slip)."""
    code = (data.get("code") or "").strip()
    if not code:
        emit("error", {"message": "code is required"})
        return
    slip = Slip.query.filter_by(code=code).first()
    if slip is not None:
        emit("error", {"message": f"slip {code} already exists"})
        return
    db.session.add(Slip(code=code, odds=0.0))
    db.session.commit()
    _emit_latest("added")


@socketio.on("single-slip")
def handle_single_slip(data):
    code = data.get("code")
    if not code:
        return
    slip = _fetch_slip(code)
    if slip:
        emit("single", slip)


@socketio.on("generate")
def handle_generate(data):
    if not (data.get("start") and data.get("country")):
        return
    country = data["country"]

    # Kick off the scrape pipeline in the worker.
    async_result = celery.send_task(
        "app.utils.celerytasks.scrape_slip_codes",
        kwargs={"country": country, "n": int(data.get("n", 10))},
    )
    # Notify start so the UI can show the "generating" spinner.
    emit(
        "data",
        {"activity": "generation-start", "data": _fetch_slips()},
    )

    # Wait for the result off the event loop so the UI stays responsive.
    def _await_result(result, country_: str) -> None:
        try:
            summary = result.get(timeout=1800, propagate=True)
            with suppress(Exception):
                socketio.emit(
                    "data",
                    {
                        "activity": "generation-done",
                        "country": country_,
                        "data": _fetch_slips(),
                        "summary": summary,
                    },
                )
        except Exception as exc:  # noqa: BLE001 - surface any worker failure
            with suppress(Exception):
                socketio.emit(
                    "error",
                    {"message": f"generation failed: {exc}"},
                )

    threading.Thread(
        target=_await_result,
        args=(async_result, country),
        daemon=True,
    ).start()


@socketio.on_error()
def handle_error(exc):
    emit("error", {"message": str(exc)})


def iso_now() -> str:
    return to_iso(datetime.now(UTC)) or ""


def register_socket_handlers() -> None:
    """No-op: handlers are registered by import via the ``@socketio.on``
    decorators above. Kept as an explicit hook so the app factory is clear
    about what side effects importing this module has."""
