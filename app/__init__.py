# celery = make_celery(flask_app)

# @celery.task()
# def get_dog_pics(breed_type, limit):
#     pass

import os
from flask import Flask, render_template
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from app.config import DevelopmentConfig

from app.utils.celeryinit import make_celery

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
celery = make_celery(app)


from app.models import Bet, Country, League, Match, Player, Slip, TeamAtt, Team


@app.route('/')
def home():
    return "hooray!!!"