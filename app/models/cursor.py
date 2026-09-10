from datetime import UTC, datetime

from sqlalchemy import DateTime

from app.extensions import db
from app.utils.serializers import model_to_dict


def utcnow() -> datetime:
    return datetime.now(UTC)


class SlipCursor(db.Model):
    """Per-country marker for the next generated slip code.

    This is the old ``Zero`` table, made relational: exactly one row per
    country, holding the last-used slip code so code generation continues
    the sequence instead of replaying it.
    """

    __tablename__ = "slip_cursor"

    id = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(255), nullable=False)
    country = db.Column(db.String(255), nullable=False, unique=True, index=True)
    created_at = db.Column(DateTime(timezone=True), nullable=False, default=utcnow)

    def as_dict(self) -> dict:
        return model_to_dict(self)

    def __repr__(self) -> str:
        return f"<SlipCursor: {self.country}={self.code}>"
