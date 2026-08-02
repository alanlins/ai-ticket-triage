from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class TicketCreateRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)


class TicketResponse(BaseModel):
    id: int
    subject: str
    body: str
    category: Literal["technical", "billing", "account", "feature_request", "other"]
    priority: Literal["low", "medium", "high", "critical"]
    summary: str
    suggested_response: str
    created_at: datetime

    class Config:
        from_attributes = True


class ClassificationResult(BaseModel):
    category: Literal["technical", "billing", "account", "feature_request", "other"]
    priority: Literal["low", "medium", "high", "critical"]
    summary: str
    suggested_response: str


class TicketsListResponse(BaseModel):
    tickets: list[TicketResponse]
    total: int
    limit: int
    offset: int


class StatsResponse(BaseModel):
    total_tickets: int
    by_category: dict[str, int]
    by_priority: dict[str, int]


class HealthResponse(BaseModel):
    status: str


class ErrorResponse(BaseModel):
    detail: str
