from questionsapp import celery, create_app
from questionsapp.celery_utils import init_celery
app = create_app()
init_celery(celery, app)
