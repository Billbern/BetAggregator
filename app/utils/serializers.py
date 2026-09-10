"""Small serialization helpers for sending model instances to the UI over
Socket.IO / JSON."""

from __future__ import annotations

from datetime import UTC, datetime


def to_iso(value: datetime | None) -> str | None:
    """Serialize a datetime to ISO-8601 (UTC, `Z` suffix) for the browser."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def model_to_dict(instance, *, relations: tuple[str, ...] = ()) -> dict:
    """Serialize a SQLAlchemy model to a plain dict (datetime-aware)."""
    data: dict = {}
    for column in instance.__table__.columns:
        value = getattr(instance, column.name)
        data[column.name] = to_iso(value) if isinstance(value, datetime) else value
    for relation in relations:
        items = getattr(instance, relation)
        data[relation] = [model_to_dict(item) for item in items]
    return data
