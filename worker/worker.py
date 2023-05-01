import os
from celery import Celery
# from app.tasks import get_result_from_GPT_task


broker_url = os.environ.get("CELERY_BROKER_URL"),
res_backend = os.environ.get("CELERY_RESULT_BACKEND")

celery_app = Celery(name='worker',
                    broker=broker_url,
                    result_backend=res_backend)

__all__ = ['celery_app']