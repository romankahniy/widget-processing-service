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
    db_widget = Widget(
        name=widget.name,
        complexity_score=widget.complexity_score,
        status=WidgetStatus.PENDING
    )

    db.add(db_widget)
    db.commit()
    db.refresh(db_widget)

    process_widget.delay(db_widget.id)

    return WidgetCreateResponse(
        widget_id=db_widget.id,
        status=db_widget.status.value
    )


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
