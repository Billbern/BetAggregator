import os
from flask import Flask, render_template
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import logging

from app.config import DevelopmentConfig
from app.config.celeryconfig import make_celery

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
logging.basicConfig(filename='betaggregator.log', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
celery = make_celery(app)


from app.models import Bet, Country, League, Match, Player, Slip, TeamAtt, Team


@app.route('/')
def home():
    return "hooray!!!"