from flask import Flask
from flask_cors import CORS
from .celery_utils import init_celery
from celery import Celery
from database import db
import os


def make_celery(app_name=__name__):
    return Celery(app_name, backend=os.getenv('CELERY_RESULT_BACKEND'), broker=os.getenv('CELERY_BROKER_URL'))

celery=make_celery()


def create_app(**kwargs):
    """Construct the core application."""
    app = Flask(__name__)
    
    if int(os.getenv('PROD')) == 1:
        app.config.from_object('config.ProdConfig')
    else:
        app.config.from_object('config.DevConfig')

    if kwargs.get("celery"):
        init_celery(kwargs.get("celery"), app)
    CORS(app)
    db.init_app(app)

    with app.app_context():
        from . import routes
        return app