from app import db


class Team(db.Model):
    __tablename__ = 'team'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    matches = db.relationship('Match', backref='team')
    teamatt_id = db.Column(db.Integer, db.ForeignKey('teamatt.id'))

    def __repr__(self):
        return '<Team: {}>'.format(self.name)
