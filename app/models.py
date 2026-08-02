from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # technical, billing, account, feature_request, other
    priority = Column(String(50), nullable=False)  # low, medium, high, critical
    summary = Column(Text, nullable=False)
    suggested_response = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "subject": self.subject,
            "body": self.body,
            "category": self.category,
            "priority": self.priority,
            "summary": self.summary,
            "suggested_response": self.suggested_response,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
