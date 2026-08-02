import json
import os
from typing import Optional
from anthropic import Anthropic
from app.schemas import ClassificationResult


class ClassificationError(Exception):
    """Raised when ticket classification fails."""
    pass


class TicketClassifier:
    def __init__(self, client: Optional[Anthropic] = None):
        """
        Initialize the ticket classifier.

        Args:
            client: Optional Anthropic client. If not provided, uses env var ANTHROPIC_API_KEY.
        """
        self.client = client or self._create_client()
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

    @staticmethod
    def _create_client() -> Anthropic:
        """Create an Anthropic client, checking that the API key is set."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ClassificationError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Please obtain a Claude API key from https://console.anthropic.com and set it in your .env file."
            )
        return Anthropic(api_key=api_key)

    def classify(self, subject: str, body: str) -> ClassificationResult:
        """
        Classify a support ticket using Claude.

        Args:
            subject: Ticket subject line
            body: Ticket body/description

        Returns:
            ClassificationResult with category, priority, summary, and suggested_response

        Raises:
            ClassificationError if classification fails after retry
        """
        prompt = self._build_prompt(subject, body)

        # Try classification with initial prompt
        try:
            result = self._call_claude(prompt)
            return result
        except (json.JSONDecodeError, ValueError) as e:
            # Retry with stricter prompt
            strict_prompt = self._build_strict_prompt(subject, body)
            try:
                result = self._call_claude(strict_prompt)
                return result
            except (json.JSONDecodeError, ValueError) as retry_error:
                raise ClassificationError(
                    f"Failed to parse Claude's response after retry. "
                    f"Initial error: {str(e)}, Retry error: {str(retry_error)}"
                )

    def _call_claude(self, prompt: str) -> ClassificationResult:
        """
        Call Claude API and parse the response.

        Args:
            prompt: The prompt to send to Claude

        Returns:
            Validated ClassificationResult

        Raises:
            json.JSONDecodeError if response is not valid JSON
            ValueError if JSON doesn't match expected schema
        """
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        response_text = message.content[0].text

        # Parse JSON from response, tolerating markdown code fences that
        # models sometimes add even when told to output raw JSON only.
        parsed = json.loads(self._strip_code_fences(response_text))

        # Validate against schema
        result = ClassificationResult(**parsed)
        return result

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        """Strip a leading/trailing ```json ... ``` or ``` ... ``` fence, if present."""
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = stripped.split("\n", 1)[1] if "\n" in stripped else stripped[3:]
            if stripped.endswith("```"):
                stripped = stripped[: -3]
            elif "```" in stripped:
                stripped = stripped.rsplit("```", 1)[0]
        return stripped.strip()

    @staticmethod
    def _build_prompt(subject: str, body: str) -> str:
        """Build the initial classification prompt."""
        return f"""Analyze the following support ticket and return ONLY a JSON object with these exact keys:
- category: one of ["technical", "billing", "account", "feature_request", "other"]
- priority: one of ["low", "medium", "high", "critical"]
- summary: 1-2 sentence summary of the issue
- suggested_response: 2-4 sentence draft reply a support agent could send

Ticket Subject: {subject}
Ticket Body: {body}

Return ONLY the JSON object, nothing else. No markdown, no explanation, no extra text."""

    @staticmethod
    def _build_strict_prompt(subject: str, body: str) -> str:
        """Build a stricter prompt for retry, with explicit format instructions."""
        return f"""You are a support ticket triage system. Analyze this ticket and respond with ONLY valid JSON.

Ticket Subject: {subject}
Ticket Body: {body}

Respond with ONLY this JSON structure, no other text:
{{
  "category": "technical" or "billing" or "account" or "feature_request" or "other",
  "priority": "low" or "medium" or "high" or "critical",
  "summary": "1-2 sentence summary",
  "suggested_response": "2-4 sentence suggested response"
}}

Output ONLY the JSON. Do not include any markdown formatting, explanation, or extra text."""
