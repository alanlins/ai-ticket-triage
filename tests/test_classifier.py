import pytest
import json
from unittest.mock import MagicMock, patch
from app.services.classifier import TicketClassifier, ClassificationError
from app.schemas import ClassificationResult


class TestTicketClassifier:
    """Tests for the TicketClassifier service."""

    def test_successful_classification(self):
        """Test successful ticket classification."""
        # Mock response from Claude
        mock_response = {
            "category": "technical",
            "priority": "high",
            "summary": "User experiencing login issues.",
            "suggested_response": "We're sorry to hear about the login issue. Please try clearing your browser cache and cookies."
        }

        # Create mock Anthropic client
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=json.dumps(mock_response))]
        mock_client.messages.create.return_value = mock_message

        classifier = TicketClassifier(client=mock_client)

        # Classify a ticket
        result = classifier.classify(
            subject="Can't log in to my account",
            body="I tried logging in multiple times but it keeps saying wrong password"
        )

        # Verify result
        assert isinstance(result, ClassificationResult)
        assert result.category == "technical"
        assert result.priority == "high"
        assert result.summary == "User experiencing login issues."
        assert result.suggested_response.startswith("We're sorry")

    def test_invalid_json_response_retries(self):
        """Test that invalid JSON triggers a retry with stricter prompt."""
        # First call returns invalid JSON, second call returns valid JSON
        mock_response_valid = {
            "category": "billing",
            "priority": "medium",
            "summary": "Payment declined.",
            "suggested_response": "We're having trouble processing your payment."
        }

        mock_client = MagicMock()
        mock_message_invalid = MagicMock()
        mock_message_invalid.content = [MagicMock(text="This is not JSON")]
        mock_message_valid = MagicMock()
        mock_message_valid.content = [MagicMock(text=json.dumps(mock_response_valid))]

        # Configure mock to return invalid first, then valid
        mock_client.messages.create.side_effect = [
            mock_message_invalid,
            mock_message_valid,
        ]

        classifier = TicketClassifier(client=mock_client)

        # Classify should retry and succeed
        result = classifier.classify(
            subject="Payment failed",
            body="My card was declined"
        )

        assert result.category == "billing"
        assert result.priority == "medium"
        # Verify that API was called twice (retry)
        assert mock_client.messages.create.call_count == 2

    def test_invalid_json_response_twice_raises_error(self):
        """Test that two consecutive JSON failures raise an error."""
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Still not JSON")]

        mock_client.messages.create.return_value = mock_message

        classifier = TicketClassifier(client=mock_client)

        # Should raise error after retry fails
        with pytest.raises(ClassificationError) as exc_info:
            classifier.classify(
                subject="Test",
                body="Test body"
            )

        assert "Failed to parse Claude's response" in str(exc_info.value)

    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises a clear error."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ClassificationError) as exc_info:
                TicketClassifier()

            assert "ANTHROPIC_API_KEY" in str(exc_info.value)
            assert "console.anthropic.com" in str(exc_info.value)

    def test_invalid_enum_values_raise_error(self):
        """Test that invalid enum values in response raise validation error."""
        # Response with invalid category
        mock_response = {
            "category": "invalid_category",
            "priority": "high",
            "summary": "Test",
            "suggested_response": "Test"
        }

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=json.dumps(mock_response))]
        mock_client.messages.create.return_value = mock_message

        classifier = TicketClassifier(client=mock_client)

        # Should fail validation and trigger retry
        with pytest.raises(ClassificationError):
            classifier.classify("Test", "Test body")

    def test_markdown_fenced_json_is_parsed(self):
        """Claude sometimes wraps JSON in ```json fences despite instructions not to."""
        mock_response = {
            "category": "feature_request",
            "priority": "low",
            "summary": "User wants dark mode.",
            "suggested_response": "Thanks for the suggestion, we'll pass it to the team.",
        }
        fenced_text = "```json\n" + json.dumps(mock_response) + "\n```"

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=fenced_text)]
        mock_client.messages.create.return_value = mock_message

        classifier = TicketClassifier(client=mock_client)

        result = classifier.classify(subject="Dark mode please", body="Would love a dark theme")

        assert result.category == "feature_request"
        assert result.priority == "low"
        # Should succeed on the first call, no retry needed.
        assert mock_client.messages.create.call_count == 1

    def test_classifier_uses_configured_model(self):
        """Test that classifier uses the model from environment."""
        with patch.dict('os.environ', {'ANTHROPIC_MODEL': 'claude-opus-4-1-20250805'}):
            mock_client = MagicMock()
            mock_message = MagicMock()
            mock_message.content = [MagicMock(text=json.dumps({
                "category": "technical",
                "priority": "low",
                "summary": "Test",
                "suggested_response": "Test"
            }))]
            mock_client.messages.create.return_value = mock_message

            classifier = TicketClassifier(client=mock_client)

            # Verify model is set
            assert classifier.model == 'claude-opus-4-1-20250805'

            classifier.classify("Test", "Test body")

            # Verify that the model was passed to the API call
            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert call_kwargs['model'] == 'claude-opus-4-1-20250805'
