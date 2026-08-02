import pytest
import os
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Test database setup - must happen before app imports
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test database with SQLite proper configuration for testing
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

from app.models import Base
Base.metadata.create_all(bind=test_engine)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db():
    """Provide test database session for each test."""
    # Clear all tables before each test
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    session = TestSessionLocal()

    yield session

    session.close()


@pytest.fixture
def client(db):
    """Create a TestClient with the test database."""
    from app.database import get_db
    from app.main import app

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    return TestClient(app)


@pytest.fixture
def mock_classifier():
    """Create a mock Anthropic classifier for testing."""
    with patch('app.routes.tickets.TicketClassifier') as mock:
        classifier_instance = MagicMock()
        mock.return_value = classifier_instance
        yield classifier_instance
