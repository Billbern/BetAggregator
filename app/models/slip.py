from datetime import UTC, datetime

from sqlalchemy import DateTime

from app.extensions import db
from app.utils.serializers import model_to_dict, to_iso


def utcnow() -> datetime:
    return datetime.now(UTC)


class Slip(db.Model):
    """A unique bet slip identified by its public code."""

    __tablename__ = "slip"

    id = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(255), nullable=False, unique=True, index=True)
    odds = db.Column(db.Float(), nullable=False, default=0.0)
    expired = db.Column(db.Boolean(), nullable=False, default=False)
    created_at = db.Column(DateTime(timezone=True), nullable=False, default=utcnow)
    expiry_date = db.Column(DateTime(timezone=True), nullable=True)

    # Flat games (what the scrapers return and the UI renders).
    games = db.relationship("Game", backref="slip", lazy=True)

    # Normalized sport graph (existing richer schema; fed by later batches).
    bet_odds = db.relationship("Bet", backref="slip")
    matches = db.relationship("Match", backref="slip")

    def as_dict(self) -> dict:
        return model_to_dict(self, relations=("games",))

    def as_display(self) -> dict:
        """Compact summary used for the slip list in the UI.

        Datetimes are ISO-serialized so the payload survives JSON
        transport (Socket.IO / REST), not just SQLAlchemy's own session.
        """
        return {
            "id": self.id,
            "code": self.code,
            "odds": self.odds,
            "expired": self.expired,
            "created_at": to_iso(self.created_at),
            "expiry_date": to_iso(self.expiry_date),
            "games": len(self.games),
        }

    def __repr__(self) -> str:
        return f"<Slip: {self.code}>"
