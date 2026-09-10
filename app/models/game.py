from datetime import UTC, datetime

from sqlalchemy import DateTime

from app.extensions import db
from app.utils.serializers import model_to_dict


def utcnow() -> datetime:
    return datetime.now(UTC)


class Game(db.Model):
    """A single selection (market) inside a betting slip.

    Mirrors the proven flat structure from the original bet-slip-generator
    product: one Game row per market the bookmaker returned for a slip code.
    """

    __tablename__ = "game"

    id = db.Column(db.Integer(), primary_key=True)
    match = db.Column(db.Text(), nullable=False)
    option = db.Column(db.String(255), nullable=False)
    odds = db.Column(db.Float(), nullable=False)
    expiry = db.Column(db.Boolean(), default=False)
    match_date = db.Column(DateTime(timezone=True), nullable=True)
    created_at = db.Column(DateTime(timezone=True), nullable=False, default=utcnow)
    slip_id = db.Column(db.Integer, db.ForeignKey("slip.id"), nullable=False, index=True)

    def as_dict(self) -> dict:
        return model_to_dict(self)

    def __repr__(self) -> str:
        return f"<Game: {self.option} @ {self.odds}>"
