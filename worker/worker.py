import os
from celery import Celery

broker_url = os.environ.get("CELERY_BROKER_URL"),
res_backend = os.environ.get("CELERY_RESULT_BACKEND")

celery_app = Celery(name='worker',
                    broker=broker_url,
                    result_backend=res_backend)


@celery_app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))