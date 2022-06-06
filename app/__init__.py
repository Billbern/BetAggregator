# import os
# import celery
# from dotenv import load_dotenv
# from celery import Celery
# from flask import Flask, render_template
# import requests
# import json


# load_dotenv()

# def make_celery(app):
#     celery = Celery(
#         app.import_name,
#         backend=app.config['CELERY_BACKEND_URL'],
#         broker=app.config['CELERY_BROKER_URL']
#     )
    
#     celery.conf.update(app.config)
    
#     class ContextTask(celery.Task):
        
#         def __call__(self, *args, **kwds):
#             with app.app_context():
#                 return self.run(*args, **kwds)
    
#     celery.Task = ContextTask
#     return celery


# flask_app = Flask(__name__)
# flask_app.config.update(
#     CELERY_BROKER_URL=os.environ.get('CELERY_BROKER_URL'),
#     CELERY_BACKEND_URL=os.environ.get('CELERY_BACKEND_URL'),
# )


# celery = make_celery(flask_app)

# @celery.task()
# def get_dog_pics(breed_type, limit):
#     pass

import os
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from app.config import DevelopmentConfig

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


from app.models import Bet, Country, League, Match, Player, Slip, TeamAtt, Team


@app.route('/')
def home():
    return "hooray!!!"