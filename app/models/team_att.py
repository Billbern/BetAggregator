from app import db


class TeamAtt(db.Model):
    __tablename__ = 'teamatt'

    id = db.Column(db.Integer(), primary_key=True)
    position = db.Column(db.Integer(), nullable=False)
    points = db.Column(db.Integer(), nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey('league.id'))
    players = db.relationship('Player', backref='teamatt')

    def __repr__(self):
        return '<{}>'.format(self.code)
