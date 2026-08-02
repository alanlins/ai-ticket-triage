from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.database import get_db
from app.models import Ticket
from app.schemas import (
    TicketCreateRequest,
    TicketResponse,
    TicketsListResponse,
    StatsResponse,
    ErrorResponse,
)
from app.services.classifier import TicketClassifier, ClassificationError

router = APIRouter(prefix="/api", tags=["tickets"])


@router.post("/tickets", response_model=TicketResponse, status_code=201)
def create_ticket(
    request: TicketCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Create a new support ticket and classify it using Claude.

    Returns the ticket with classification results.
    """
    try:
        classifier = TicketClassifier()
    except ClassificationError as e:
        # API key not set
        raise HTTPException(
            status_code=503,
            detail=str(e),
        )

    try:
        # Classify the ticket
        classification = classifier.classify(request.subject, request.body)
    except ClassificationError as e:
        # Classification failed
        raise HTTPException(
            status_code=502,
            detail=f"Failed to classify ticket: {str(e)}",
        )

    # Create ticket record
    ticket = Ticket(
        subject=request.subject,
        body=request.body,
        category=classification.category,
        priority=classification.priority,
        summary=classification.summary,
        suggested_response=classification.suggested_response,
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return TicketResponse.model_validate(ticket)


@router.get("/tickets", response_model=TicketsListResponse)
def list_tickets(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: str | None = Query(None),
    priority: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    List tickets with optional filtering and pagination.

    Query parameters:
    - limit: number of tickets per page (default 20, max 100)
    - offset: number of tickets to skip (default 0)
    - category: filter by category (technical, billing, account, feature_request, other)
    - priority: filter by priority (low, medium, high, critical)
    """
    query = db.query(Ticket).order_by(desc(Ticket.created_at), desc(Ticket.id))

    # Apply filters
    if category:
        query = query.filter(Ticket.category == category)
    if priority:
        query = query.filter(Ticket.priority == priority)

    # Get total count
    total = query.count()

    # Apply pagination
    tickets = query.limit(limit).offset(offset).all()

    return TicketsListResponse(
        tickets=[TicketResponse.model_validate(t) for t in tickets],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Get a single ticket by ID."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return TicketResponse.model_validate(ticket)


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """
    Get aggregate statistics about tickets.

    Returns:
    - total_tickets: total number of tickets
    - by_category: counts grouped by category
    - by_priority: counts grouped by priority
    """
    total = db.query(func.count(Ticket.id)).scalar() or 0

    # Group by category
    category_counts = db.query(Ticket.category, func.count(Ticket.id)).group_by(
        Ticket.category
    ).all()
    by_category = {cat: count for cat, count in category_counts}

    # Group by priority
    priority_counts = db.query(Ticket.priority, func.count(Ticket.id)).group_by(
        Ticket.priority
    ).all()
    by_priority = {pri: count for pri, count in priority_counts}

    return StatsResponse(
        total_tickets=total,
        by_category=by_category,
        by_priority=by_priority,
    )
