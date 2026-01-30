import os
import time
import random
from celery import Celery
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Widget, WidgetStatus
from app.utils import contains_palindrome, is_prime


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "widget_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def process_widget(self, widget_id: int):
    db: Session = SessionLocal()

    try:
        widget = db.query(Widget).filter(Widget.id == widget_id).first()

        if not widget:
            raise ValueError(f"Widget with id {widget_id} not found")

        processing_time = random.uniform(5, 15)
        time.sleep(processing_time)

        success = determine_widget_outcome(widget.name, widget.complexity_score)

        if success:
            widget.status = WidgetStatus.SUCCESS
        else:
            widget.status = WidgetStatus.FAILED

        db.commit()

        return {
            "widget_id": widget_id,
            "status": widget.status.value,
            "processing_time": processing_time
        }

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)

    finally:
        db.close()


def determine_widget_outcome(name: str, complexity_score: int) -> bool:
    if contains_palindrome(name, min_length=3):
        return True

    if is_prime(complexity_score):
        return random.random() > 0.15

    return random.random() < 0.80
