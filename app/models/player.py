from app import db


class Player(db.Model):
    __tablename__ = 'player'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    teamatt_id = db.Column(db.Integer, db.ForeignKey('teamatt.id'))

    def __repr__(self):
        return '<Player: {}>'.format(self.name)
