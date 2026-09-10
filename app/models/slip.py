from app.extensions import db


class Slip(db.Model):
    __tablename__ = "slip"

    id = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(255), nullable=False)
    bet_odds = db.relationship("Bet", backref="slip")
    matches = db.relationship("Match", backref="slip")

    def __repr__(self):
        return f"<Slip: {self.code}>"
