from app.extensions import db


class Team(db.Model):
    __tablename__ = "team"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    # A team can appear as the home or away side of a match, hence two
    # explicit foreign-key relationships (avoids ambiguity for the mapper).
    home_matches = db.relationship("Match", foreign_keys="Match.home_id", backref="home_team")
    away_matches = db.relationship("Match", foreign_keys="Match.away_id", backref="away_team")
    teamatt_id = db.Column(db.Integer, db.ForeignKey("teamatt.id"))

    def __repr__(self):
        return f"<Team: {self.name}>"
