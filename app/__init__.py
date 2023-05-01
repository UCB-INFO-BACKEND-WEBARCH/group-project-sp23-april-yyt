from flask import Flask
from celery import Celery

app = Flask(__name__)


from app import views
