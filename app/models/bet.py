from app import db


class Bet(db.Model):
    __tablename__ = 'bet'

    id = db.Column(db.Integer(), primary_key=True)
    odds = db.Column(db.Float() , nullable=False)
    outcome = db.Column(db.String(255), nullable=False)
    bettype = db.Column(db.String(255), nullable=False)
    slip_id = db.Column(db.Integer, db.ForeignKey('slip.id'))

    def __repr__(self):
        return '<{} @ {}>'.format(self.outcome, self.odds)
