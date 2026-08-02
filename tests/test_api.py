import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
from app.schemas import ClassificationResult


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test /health endpoint returns ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestCreateTicketEndpoint:
    """Tests for POST /api/tickets endpoint."""

    def test_create_ticket_success(self, client):
        """Test successful ticket creation and classification."""
        # Mock the classifier
        with patch('app.routes.tickets.TicketClassifier') as mock_classifier_class:
            mock_classifier = MagicMock()
            mock_classifier.classify.return_value = ClassificationResult(
                category="technical",
                priority="high",
                summary="User cannot access account.",
                suggested_response="We're here to help! Please verify your account details."
            )
            mock_classifier_class.return_value = mock_classifier

            response = client.post("/api/tickets", json={
                "subject": "Can't access account",
                "body": "I've tried resetting my password but still can't log in."
            })

            assert response.status_code == 201
            data = response.json()
            assert data["subject"] == "Can't access account"
            assert data["category"] == "technical"
            assert data["priority"] == "high"
            assert data["summary"] == "User cannot access account."
            assert data["suggested_response"] == "We're here to help! Please verify your account details."
            assert "id" in data
            assert "created_at" in data

    def test_create_ticket_missing_api_key(self, client):
        """Test that missing API key returns 503 with clear error message."""
        from app.services.classifier import ClassificationError

        with patch('app.routes.tickets.TicketClassifier') as mock_classifier_class:
            mock_classifier_class.side_effect = ClassificationError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Please obtain a Claude API key from https://console.anthropic.com"
            )

            response = client.post("/api/tickets", json={
                "subject": "Test",
                "body": "Test ticket"
            })

            assert response.status_code == 503
            data = response.json()
            assert "ANTHROPIC_API_KEY" in data["detail"]
            assert "console.anthropic.com" in data["detail"]

    def test_create_ticket_classification_failure(self, client):
        """Test that classification errors return 502."""
        from app.services.classifier import ClassificationError

        with patch('app.routes.tickets.TicketClassifier') as mock_classifier_class:
            mock_classifier = MagicMock()
            mock_classifier.classify.side_effect = ClassificationError("Failed to parse response")
            mock_classifier_class.return_value = mock_classifier

            response = client.post("/api/tickets", json={
                "subject": "Test",
                "body": "Test ticket"
            })

            assert response.status_code == 502
            assert "Failed to classify ticket" in response.json()["detail"]

    def test_create_ticket_validation_error_empty_subject(self, client):
        """Test that empty subject is rejected."""
        response = client.post("/api/tickets", json={
            "subject": "",
            "body": "Test body"
        })

        assert response.status_code == 422

    def test_create_ticket_validation_error_missing_body(self, client):
        """Test that missing body is rejected."""
        response = client.post("/api/tickets", json={
            "subject": "Test subject"
        })

        assert response.status_code == 422


class TestListTicketsEndpoint:
    """Tests for GET /api/tickets endpoint."""

    def test_list_tickets_empty(self, client):
        """Test listing tickets when none exist."""
        response = client.get("/api/tickets")
        assert response.status_code == 200
        data = response.json()
        assert data["tickets"] == []
        assert data["total"] == 0
        assert data["limit"] == 20
        assert data["offset"] == 0

    def test_list_tickets_with_pagination(self, client):
        """Test listing tickets with pagination parameters."""
        # Create some test tickets
        with patch('app.routes.tickets.TicketClassifier') as mock_classifier_class:
            mock_classifier = MagicMock()
            mock_classifier.classify.return_value = ClassificationResult(
                category="technical",
                priority="high",
                summary="Test",
                suggested_response="Test"
            )
            mock_classifier_class.return_value = mock_classifier

            # Create 3 tickets
            for i in range(3):
                client.post("/api/tickets", json={
                    "subject": f"Ticket {i}",
                    "body": f"Body {i}"
                })

        # List with limit and offset
        response = client.get("/api/tickets?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tickets"]) == 2
        assert data["total"] == 3
        assert data["limit"] == 2
        assert data["offset"] == 0

    def test_list_tickets_filter_by_category(self, client):
        """Test filtering tickets by category."""
        with patch('app.routes.tickets.TicketClassifier') as mock_classifier_class:
            mock_classifier = MagicMock()
            mock_classifier_class.return_value = mock_classifier

            # Create tickets with different categories
            mock_classifier.classify.side_effect = [
                ClassificationResult(
                    category="technical",
                    priority="high",
                    summary="Tech issue",
                    suggested_response="Tech response"
                ),
                ClassificationResult(
                    category="billing",
                    priority="medium",
                    summary="Billing issue",
                    suggested_response="Billing response"
                ),
            ]

            client.post("/api/tickets", json={
                "subject": "Tech issue",
                "body": "Body"
            })
            client.post("/api/tickets", json={
                "subject": "Billing issue",
                "body": "Body"
            })

        # Filter by category
        response = client.get("/api/tickets?category=technical")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tickets"]) == 1
        assert data["tickets"][0]["category"] == "technical"

    def test_list_tickets_filter_by_priority(self, client):
        """Test filtering tickets by priority."""
        with patch('app.routes.tickets.TicketClassifier') as mock_classifier_class:
            mock_classifier = MagicMock()
            mock_classifier_class.return_value = mock_classifier

            # Create tickets with different priorities
            mock_classifier.classify.side_effect = [
                ClassificationResult(
                    category="technical",
                    priority="high",
                    summary="High priority",
                    suggested_response="Response"
                ),
                ClassificationResult(
                    category="technical",
                    priority="low",
                    summary="Low priority",
                    suggested_response="Response"
                ),
            ]

            client.post("/api/tickets", json={
                "subject": "High priority",
                "body": "Body"
            })
            client.post("/api/tickets", json={
                "subject": "Low priority",
                "body": "Body"
            })

        # Filter by priority
        response = client.get("/api/tickets?priority=high")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tickets"]) == 1
        assert data["tickets"][0]["priority"] == "high"

    def test_list_tickets_ordered_newest_first(self, client):
        """Test that tickets are ordered by creation date, newest first."""
        with patch('app.routes.tickets.TicketClassifier') as mock_classifier_class:
            mock_classifier = MagicMock()
            mock_classifier.classify.return_value = ClassificationResult(
                category="technical",
                priority="high",
                summary="Test",
                suggested_response="Test"
            )
            mock_classifier_class.return_value = mock_classifier

            # Create tickets
            response1 = client.post("/api/tickets", json={
                "subject": "First",
                "body": "Body"
            })
            response2 = client.post("/api/tickets", json={
                "subject": "Second",
                "body": "Body"
            })

            id1 = response1.json()["id"]
            id2 = response2.json()["id"]

        # List and verify order
        response = client.get("/api/tickets")
        data = response.json()
        # Second ticket should be first (newer)
        assert data["tickets"][0]["id"] == id2
        assert data["tickets"][1]["id"] == id1


class TestGetTicketEndpoint:
    """Tests for GET /api/tickets/{id} endpoint."""

    def test_get_ticket_success(self, client):
        """Test getting a single ticket."""
        with patch('app.routes.tickets.TicketClassifier') as mock_classifier_class:
            mock_classifier = MagicMock()
            mock_classifier.classify.return_value = ClassificationResult(
                category="technical",
                priority="high",
                summary="Test",
                suggested_response="Response"
            )
            mock_classifier_class.return_value = mock_classifier

            # Create a ticket
            create_response = client.post("/api/tickets", json={
                "subject": "Test",
                "body": "Test body"
            })
            ticket_id = create_response.json()["id"]

        # Get the ticket
        response = client.get(f"/api/tickets/{ticket_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ticket_id
        assert data["subject"] == "Test"
        assert data["body"] == "Test body"

    def test_get_ticket_not_found(self, client):
        """Test getting a nonexistent ticket."""
        response = client.get("/api/tickets/99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Ticket not found"


class TestStatsEndpoint:
    """Tests for GET /api/stats endpoint."""

    def test_stats_empty(self, client):
        """Test stats when no tickets exist."""
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_tickets"] == 0
        assert data["by_category"] == {}
        assert data["by_priority"] == {}

    def test_stats_with_tickets(self, client):
        """Test stats with various tickets."""
        with patch('app.routes.tickets.TicketClassifier') as mock_classifier_class:
            mock_classifier = MagicMock()
            mock_classifier_class.return_value = mock_classifier

            # Create tickets with various categories and priorities
            mock_classifier.classify.side_effect = [
                ClassificationResult(
                    category="technical",
                    priority="high",
                    summary="Test",
                    suggested_response="Test"
                ),
                ClassificationResult(
                    category="technical",
                    priority="low",
                    summary="Test",
                    suggested_response="Test"
                ),
                ClassificationResult(
                    category="billing",
                    priority="high",
                    summary="Test",
                    suggested_response="Test"
                ),
            ]

            client.post("/api/tickets", json={"subject": "T1", "body": "B"})
            client.post("/api/tickets", json={"subject": "T2", "body": "B"})
            client.post("/api/tickets", json={"subject": "T3", "body": "B"})

        # Get stats
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_tickets"] == 3
        assert data["by_category"]["technical"] == 2
        assert data["by_category"]["billing"] == 1
        assert data["by_priority"]["high"] == 2
        assert data["by_priority"]["low"] == 1
