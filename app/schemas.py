from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class WidgetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    complexity_score: int = Field(..., ge=0, le=100)

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Name cannot be empty or whitespace only')
        return v.strip()


class WidgetResponse(BaseModel):
    id: int
    name: str
    complexity_score: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WidgetCreateResponse(BaseModel):
    widget_id: int
    status: str
