import redis
import hashlib
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.models import Widget, WidgetStatus
from app.schemas import WidgetCreate, WidgetCreateResponse, WidgetResponse
from app.tasks import process_widget
from app.rate_limiter import rate_limiter


app = FastAPI(
    title="Widget Processing Service",
    description="Asynchronous widget processing with quantum simulation",
    version="1.0.0"
)

redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)


@app.on_event("startup")
async def startup_event():
    init_db()


@app.post(
    "/widgets",
    response_model=WidgetCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Widgets"]
)
async def create_widget(
    widget: WidgetCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(rate_limiter.check_rate_limit)
):
    task_id = hashlib.sha256(f"{user_id}_{widget.name}_{widget.complexity_score}".encode()).hexdigest()

    widget_exist = redis_client.get(f"submission:{task_id}")
    if widget_exist:
        return WidgetCreateResponse(widget_id=int(widget_exist), status="pending")

    lock = redis_client.lock(f"lock:{task_id}", timeout=2)
    try:
        if not lock.acquire(blocking=True, blocking_timeout=1):
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable, please retry"
            )

        widget_exist = redis_client.get(f"submission:{task_id}")
        if widget_exist:
            return WidgetCreateResponse(widget_id=int(widget_exist), status="pending")

        db_widget = Widget(
            name=widget.name,
            complexity_score=widget.complexity_score,
            status=WidgetStatus.PENDING
        )

        db.add(db_widget)
        db.commit()
        db.refresh(db_widget)

        redis_client.setex(f"submission:{task_id}", 60, db_widget.id)

        process_widget.apply_async([db_widget.id], task_id=task_id)

        return WidgetCreateResponse(
            widget_id=db_widget.id,
            status=db_widget.status.value
        )

    finally:
        try:
            lock.release()
        except redis.exceptions.LockError:
            pass


@app.get(
    "/widgets/{widget_id}",
    response_model=WidgetResponse,
    tags=["Widgets"]
)
async def get_widget_status(widget_id: int, db: Session = Depends(get_db)):
    widget = db.query(Widget).filter(Widget.id == widget_id).first()

    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Widget with id {widget_id} not found"
        )

    return widget
