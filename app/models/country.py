from app import db


class Country(db.Model):
    __tablename__ = 'country'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    leagues = db.relationship('League', backref='country')

    def __repr__(self):
        return '<Country: {}>'.format(self.name)
