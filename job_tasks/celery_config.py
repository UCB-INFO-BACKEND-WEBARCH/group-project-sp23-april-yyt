from celery import Celery

app = Celery('tasks', broker='redis://job_broker:6379', backend='redis://job_broker:6379')
