from .extensions import limiter
from flask import Flask
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from .celery_utils import init_celery
from celery import Celery
from database import db
import os
from .env import get_env_bool


class Utf8JSONProvider(DefaultJSONProvider):
    def dumps(self, obj, **kwargs):
        # гарантируем ensure_ascii=False даже если где-то не передали
        kwargs.setdefault("ensure_ascii", False)
        return super().dumps(obj, **kwargs)

def make_celery(app_name=__name__):
    return Celery(app_name, backend=os.getenv('CELERY_RESULT_BACKEND'), broker=os.getenv('CELERY_BROKER_URL'))

celery=make_celery()


def create_app(**kwargs):
    """Construct legacy Flask application context for background/bridge usage.

    Notes:
    - FastAPI is the only HTTP runtime entrypoint.
    - Legacy Flask routes/templates were removed during cleanup.
    - Flask app is kept only as a compatibility container for config/DB context.
    """
    app = Flask(__name__)

    app.config['JSON_AS_ASCII'] = False
    app.json = Utf8JSONProvider(app)
    app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

    limiter.init_app(app)

    if get_env_bool('PROD'):
        app.config.from_object('config.ProdConfig')
    else:
        app.config.from_object('config.DevConfig')

    if kwargs.get("celery"):
        init_celery(kwargs.get("celery"), app)

    CORS(app)
    db.init_app(app)

    return app
