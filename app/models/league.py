from app import db


class League(db.Model):
    __tablename__ = 'league'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    matches = db.relationship('Match', backref='league')
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'))

    def __repr__(self):
        return '<League: {}>'.format(self.name)
