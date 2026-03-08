from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv(override=True)
def make_celery(app_name=__name__):
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

    print(redis_url)
    return Celery(
        app_name,
        broker=redis_url,
        backend=redis_url,
        include=["backend.celery_app.tasks"]
    )

celery = make_celery()