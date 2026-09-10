from app.extensions import db


class Bet(db.Model):
    __tablename__ = "bet"

    id = db.Column(db.Integer(), primary_key=True)
    odds = db.Column(db.Float(), nullable=False)
    outcome = db.Column(db.String(255), nullable=False)
    bettype = db.Column(db.String(255), nullable=False)
    slip_id = db.Column(db.Integer, db.ForeignKey("slip.id"))
    matches = db.relationship("Match", backref="bet")

    def __repr__(self):
        return f"<Bet: {self.outcome} @ {self.odds}>"
