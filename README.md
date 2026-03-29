# Dev Environment Request System

A REST API for managing developer environment provisioning requests. Developers submit requests for new environments with specific configurations; administrators review, approve, or reject them. The system tracks the full lifecycle from submission through provisioning and expiration.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Database Migrations](#database-migrations)
- [Development](#development)

---

## Features

- Submit environment requests with resource specs (CPU, RAM, storage), OS, tools, and duration
- Admin review workflow: approve or reject with required reason
- Full request lifecycle: `pending` → `approved` / `rejected` → `provisioning` → `active` → `expired` / `cancelled`
- Automatic expiry date calculation based on requested duration
- Paginated listing with status-based filtering
- Admin statistics endpoint for request counts by status
- Health and readiness probes (Kubernetes-compatible)
- Structured JSON logging (pretty-printed in local dev)
- OpenAPI docs auto-generated at `/docs` (disabled in production)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | [Litestar 2.x](https://litestar.dev) (ASGI) |
| ORM | SQLAlchemy 2.0 (async) + Advanced Alchemy |
| Validation | Pydantic v2 |
| Migrations | Alembic |
| Database (local) | SQLite via aiosqlite |
| Database (prod) | PostgreSQL via asyncpg |
| Server | Uvicorn |
| Logging | structlog |
| Config | Pydantic Settings |
| Linting/Formatting | Ruff |
| Git Hooks | pre-commit |

---

## Getting Started

### Prerequisites

- Python 3.11
- [PDM](https://pdm-project.org/en/latest/) package manager

### Install

```bash
pdm install
```

### Configure

Copy the example environment file and edit as needed:

```bash
cp .env.example .env
```

Key variables (see [Configuration](#configuration) for the full list).

### Run migrations

```bash
pdm run migrate-up
```

### Start the server

```bash
pdm run start
```

The API will be available at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

---

## Configuration

All configuration is via environment variables (or a `.env` file).

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `Dev Environment Request System` | Application display name |
| `APP_VERSION` | `1.0.0` | Application version |
| `DEBUG` | `false` | Enable debug mode |
| `ENV` | `local` | Environment name (`local`, `staging`, `production`) |
| `DATABASE_URL` | SQLite `dev_env.db` | Database connection URL |
| `API_PREFIX` | `/api/v1` | URL prefix for all API routes |
| `ALLOWED_ORIGINS` | `["http://localhost:3000"]` | CORS allowed origins |

**Example `DATABASE_URL` values:**

```bash
# Local (default)
DATABASE_URL=sqlite+aiosqlite:///dev_env.db

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dev_env_requests
```

---

## API Reference

### System

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Root endpoint |
| `GET` | `/health` | Liveness probe |
| `GET` | `/ready` | Readiness probe (checks DB connectivity) |

### Environment Requests

All endpoints are prefixed with `/api/v1`.

| Method | Path | Description |
|---|---|---|
| `POST` | `/environment-requests/` | Submit a new request |
| `GET` | `/environment-requests/` | List requests (paginated, filterable by status) |
| `GET` | `/environment-requests/stats` | Get request counts by status |
| `GET` | `/environment-requests/{id}` | Get a single request |
| `PATCH` | `/environment-requests/{id}` | Update a pending request |
| `DELETE` | `/environment-requests/{id}` | Delete a request |
| `PATCH` | `/environment-requests/{id}/review` | Approve or reject (admin) |
| `PATCH` | `/environment-requests/{id}/cancel` | Cancel a request |

### Request Lifecycle

```
pending ──► approved ──► provisioning ──► active ──► expired
   │            │                                        ▲
   │            └──────────────────────────────────────►─┘
   ├──► rejected
   └──► cancelled (from pending or approved)
```

Business rules:
- Only `pending` requests can be updated by the requester.
- Only `pending` requests can be reviewed by an admin.
- Rejections require a `rejection_reason`.
- Only `pending` or `approved` requests can be cancelled.
- Expiry date is set automatically at creation: `created_at + duration_days`.

### Create Request — Example Payload

```json
{
  "requester_name": "Alice Smith",
  "requester_email": "alice@example.com",
  "team": "Platform",
  "environment_name": "alice-feature-xyz",
  "environment_type": "dev",
  "os_type": "ubuntu",
  "os_version": "22.04",
  "cpu_cores": 4,
  "ram_gb": 16,
  "storage_gb": 100,
  "required_tools": ["docker", "kubectl", "python3"],
  "purpose": "Feature development for XYZ project",
  "duration_days": 14
}
```

### Review Request — Example Payload

```json
{
  "status": "approved",
  "reviewed_by": "admin@example.com"
}
```

Or to reject:

```json
{
  "status": "rejected",
  "reviewed_by": "admin@example.com",
  "rejection_reason": "Insufficient justification for storage allocation."
}
```

---

## Database Migrations

```bash
# Apply all pending migrations
pdm run migrate-up

# Rollback one migration
pdm run migrate-down

# Show current revision
pdm run migrate-current

# Show migration history
pdm run migrate-history

# Generate a new migration (after changing models)
pdm run migrate-new "describe your change here"
```

---

## Development

### Running tests

```bash
pdm run test
```

### Linting and formatting

```bash
pdm run lint      # Check with ruff
pdm run format    # Auto-format with ruff
```

### Type checking

```bash
pdm run typecheck
```

### Pre-commit hooks

Install the hooks to run linting and formatting automatically on every commit:

```bash
pre-commit install
```

---

## License

MIT — see [LICENSE](LICENSE).
