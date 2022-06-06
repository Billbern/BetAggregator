from app import db


class Match(db.Model):
    __tablename__ = 'match'

    id = db.Column(db.Integer(), primary_key=True)
    home_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    away_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    league_id = db.Column(db.Integer, db.ForeignKey('league.id'))
    bet_id = db.Column(db.Integer, db.ForeignKey('bet.id'))
    slip_id = db.Column(db.Integer, db.ForeignKey('slip.id'))

    def __repr__(self):
        return '<{} vs {}>'.format(self.home_id, self.away_id)
