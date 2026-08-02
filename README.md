# AI Ticket Triage

An AI-powered support ticket classification and intelligent response generation service. This backend service uses the Claude API to automatically classify incoming support tickets by category and priority, generate concise summaries, and suggest initial responses for support agents.

## What It Does

When a user submits a support ticket with a subject and description, the service:

1. **Classifies the ticket category** into one of: `technical`, `billing`, `account`, `feature_request`, or `other`
2. **Assigns a priority level** of `low`, `medium`, `high`, or `critical`
3. **Generates a summary** (1-2 sentences) of the issue
4. **Suggests an initial response** (2-4 sentences) that a support agent could send to the customer

All ticket data and AI-generated fields are persisted to a PostgreSQL database and can be queried via REST API.

## Stack

- **Python 3.12** with **FastAPI** for the REST API framework
- **SQLAlchemy 2.x** (declarative ORM) + **Alembic** for database migrations
- **Pydantic v2** for request/response validation
- **PostgreSQL 16** (via Docker) for persistent data storage
- **Claude API** (Anthropic) for intelligent ticket classification
- **Docker & Docker Compose** for containerized deployment
- **pytest** for comprehensive test coverage

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- A free Claude API key from https://console.anthropic.com

### Setup & Run

1. **Clone or navigate to the project:**
   ```bash
   cd C:\Users\KISUKE\PROJECTS\ai-ticket-triage
   ```

2. **Get a Claude API key:**
   - Visit https://console.anthropic.com
   - Sign up (free) and generate an API key
   - Copy your key

3. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and paste your Claude API key:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
   ```

4. **Start the service:**
   ```bash
   docker-compose up --build
   ```

   The service will:
   - Create and initialize the PostgreSQL database
   - Run database migrations automatically
   - Start the FastAPI server on `http://localhost:8000`

5. **Open the demo page:**
   Navigate to http://localhost:8000 in your browser

6. **Stop the service:**
   ```bash
   docker-compose down
   ```

## API Documentation

### Endpoints

#### `GET /` — Demo Page
Serves the interactive demo UI for submitting and viewing tickets.

#### `GET /health` — Health Check
Simple health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

#### `POST /api/tickets` — Create Ticket
Submit a new support ticket for classification.

**Request:**
```json
{
  "subject": "Can't reset password",
  "body": "I clicked forgot password but didn't receive an email reset link"
}
```

**Response (201):**
```json
{
  "id": 1,
  "subject": "Can't reset password",
  "body": "I clicked forgot password but didn't receive an email reset link",
  "category": "account",
  "priority": "high",
  "summary": "User unable to receive password reset email.",
  "suggested_response": "We're sorry for the trouble. Please check your spam folder. If you still don't see the email, we can help reset your password directly.",
  "created_at": "2025-08-01T12:34:56.789012"
}
```

**Error (503 - Missing API Key):**
```json
{
  "detail": "ANTHROPIC_API_KEY environment variable is not set. Please obtain a Claude API key from https://console.anthropic.com and set it in your .env file."
}
```

**Error (502 - Classification Failed):**
```json
{
  "detail": "Failed to classify ticket: ..."
}
```

#### `GET /api/tickets` — List Tickets
Retrieve paginated list of tickets with optional filtering.

**Query Parameters:**
- `limit` (int, default 20, max 100): Number of tickets to return
- `offset` (int, default 0): Number of tickets to skip
- `category` (string, optional): Filter by category (technical, billing, account, feature_request, other)
- `priority` (string, optional): Filter by priority (low, medium, high, critical)

**Response:**
```json
{
  "tickets": [
    {
      "id": 2,
      "subject": "Payment failed",
      "body": "My credit card was declined",
      "category": "billing",
      "priority": "high",
      "summary": "Customer's payment was rejected.",
      "suggested_response": "We apologize for the declined payment. Please verify your card details or try a different payment method.",
      "created_at": "2025-08-01T12:35:00.000000"
    }
  ],
  "total": 2,
  "limit": 20,
  "offset": 0
}
```

#### `GET /api/tickets/{id}` — Get Single Ticket
Retrieve a specific ticket by ID.

**Response (200):**
```json
{
  "id": 1,
  "subject": "Can't reset password",
  ...
}
```

**Response (404):**
```json
{
  "detail": "Ticket not found"
}
```

#### `GET /api/stats` — Aggregate Statistics
Get summary statistics about all tickets.

**Response:**
```json
{
  "total_tickets": 42,
  "by_category": {
    "technical": 18,
    "billing": 12,
    "account": 8,
    "feature_request": 3,
    "other": 1
  },
  "by_priority": {
    "critical": 2,
    "high": 15,
    "medium": 18,
    "low": 7
  }
}
```

#### `GET /docs` — Interactive API Documentation
Swagger UI with live endpoint testing.

## Database

### Schema

The `tickets` table contains:

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER | Primary key, auto-increment |
| `subject` | VARCHAR(255) | Ticket subject line |
| `body` | TEXT | Full ticket description |
| `category` | VARCHAR(50) | One of: technical, billing, account, feature_request, other |
| `priority` | VARCHAR(50) | One of: low, medium, high, critical |
| `summary` | TEXT | AI-generated 1-2 sentence summary |
| `suggested_response` | TEXT | AI-generated suggested reply |
| `created_at` | DATETIME | Timestamp, server-set to now() |

### Migrations

Migrations are managed via Alembic and run automatically on startup via Docker. To manually run migrations:

```bash
# Inside Docker container or with DATABASE_URL set
alembic upgrade head

# To create a new migration after model changes
alembic revision --autogenerate -m "Description of change"
```

## Testing

Run the full test suite:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=app --cov-report=html
```

### Test Coverage

- **Unit tests** for the Claude classifier service (mocked Anthropic client, no real API calls)
- **Integration tests** for all API endpoints (in-memory SQLite database, mocked classifier)
- Tests cover: successful classification, API key validation, missing data, filtering, pagination, error handling

**Important:** All tests mock the Anthropic API client — zero real network calls to api.anthropic.com are made during testing.

## Configuration

### Environment Variables

Create a `.env` file at the project root (copy from `.env.example`):

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional (defaults shown)
ANTHROPIC_MODEL=claude-haiku-4-5-20251001
DATABASE_URL=postgresql+psycopg://ticketuser:ticketpass@db:5432/tickets
```

The `DATABASE_URL` is automatically set by docker-compose and points to the Postgres container. You only need to set it manually when running outside Docker Compose.

## Project Structure

```
ai-ticket-triage/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── database.py             # Database configuration
│   ├── models.py               # SQLAlchemy ORM models
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── routes/
│   │   ├── __init__.py
│   │   └── tickets.py          # API route handlers
│   └── services/
│       ├── __init__.py
│       └── classifier.py       # Claude API integration & classification logic
├── static/
│   ├── index.html              # Demo page UI
│   └── app.js                  # Frontend JavaScript
├── tests/
│   ├── conftest.py             # Pytest fixtures and configuration
│   ├── test_classifier.py      # Unit tests for classifier service
│   └── test_api.py             # Integration tests for API endpoints
├── alembic/
│   ├── env.py                  # Alembic environment configuration
│   ├── versions/
│   │   └── 001_initial_create_tickets_table.py
│   └── script.py.mako
├── alembic.ini                 # Alembic configuration
├── Dockerfile                  # Container image definition
├── docker-compose.yml          # Multi-container orchestration
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── pytest.ini                  # Pytest configuration
└── README.md                   # This file
```

## Development

### Running Locally (Without Docker)

If you want to develop locally with a local PostgreSQL instance:

1. **Set up PostgreSQL:**
   - Install PostgreSQL 16
   - Create a database and user
   - Set `DATABASE_URL` environment variable

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

4. **Start the server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### Making Changes

1. **Update models** in `app/models.py`
2. **Create a new migration:**
   ```bash
   alembic revision --autogenerate -m "Description"
   ```
3. **Add tests** in `tests/`
4. **Run tests** to verify: `pytest`

## Troubleshooting

### "API Key not configured" message

**Problem:** The demo page shows an error banner about missing API key.

**Solution:**
1. Make sure you obtained a key from https://console.anthropic.com
2. Create `.env` file with: `ANTHROPIC_API_KEY=your_key_here`
3. Restart: `docker-compose up --build`

### Database connection errors

**Problem:** "connection refused" or "no such table: tickets"

**Solution:**
- Ensure docker-compose is fully started: `docker-compose logs db`
- Migrations may not have run; check the `api` service logs: `docker-compose logs api`
- You can manually run migrations: `docker-compose exec api alembic upgrade head`

### Port 8000 already in use

**Problem:** `Address already in use`

**Solution:**
- Stop other services: `docker-compose down`
- Or change the port in `docker-compose.yml` (map `"8001:8000"` instead)

## Integration with External Systems

This service is designed to be integrated into larger support platforms. Example integrations:

- **Email integration:** Forward incoming support emails to `POST /api/tickets`
- **Slack bot:** Build a Slack app that submits tickets and displays classifications
- **Help desk platforms:** Use as a middleware for Zendesk, Freshdesk, etc.
- **Custom dashboards:** Query `/api/stats` for real-time support metrics

## License

This is a portfolio project. Use freely for learning and demonstration purposes.

## Author

Alan Lins (alan.v.lins@gmail.com)

---

**Built with:** FastAPI, SQLAlchemy, PostgreSQL, Claude API, Docker
