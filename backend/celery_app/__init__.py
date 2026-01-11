from celery import Celery
import os

def make_celery(app_name=__name__):
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    return Celery(
        app_name,
        broker=redis_url,
        backend=redis_url,
        include=["backend.celery_app.tasks"]
    )

celery = make_celery()