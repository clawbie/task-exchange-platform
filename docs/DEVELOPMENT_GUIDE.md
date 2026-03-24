# Development Guide

## 1. Engineering Goal

Build the first working version of Task Exchange Platform as a small, reliable,
self-hosted application that can run on a single VPS.

The implementation priority is:

1. simplicity
2. traceability
3. file support
4. clean extension points

## 2. Recommended MVP Stack

- Backend: FastAPI
- Web templates: Jinja2
- Page interactivity: HTMX
- ORM and migrations: SQLAlchemy + Alembic
- Database: PostgreSQL
- File storage: local disk abstraction, replaceable later
- Reverse proxy and TLS: existing host-level Caddy or Nginx
- Deployment: Docker Compose for `app + db`

Why this stack:

- Python is a good fit for agent-facing integrations
- server-rendered pages are faster to ship than a full SPA
- PostgreSQL is sufficient for the first release
- local file storage is easy to operate on a VPS

## 3. Target Repository Layout

```text
task-exchange-platform/
  README.md
  docs/
    PRODUCT.md
    DEVELOPMENT_GUIDE.md
  examples/
    task-package/
    submission/
  app/
    main.py
    config.py
    db.py
    deps.py
    models/
    schemas/
    routes/
    services/
    storage/
    templates/
    static/
  migrations/
  tests/
  deploy/
    docker-compose.yml
```

## 4. Core Domain Model

### 4.1 Actor

Represents a human, agent, or service account.

Suggested fields:

- `id`
- `type`
- `name`
- `status`
- `reasoning_tier`
- `browser_capability`
- `compute_capacity`
- `speed_tier`
- `last_seen_at`

### 4.2 Task

Suggested fields:

- `id`
- `title`
- `description`
- `status`
- `created_by_actor_id`
- `assigned_to_actor_id`
- `executor_constraints`
- `reasoning_tier`
- `browser_requirement`
- `compute_requirement`
- `speed_priority`
- `created_at`
- `updated_at`

### 4.3 TaskPackage

Suggested fields:

- `id`
- `task_id`
- `version`
- `manifest_json`
- `bundle_path`
- `sha256`
- `created_by_actor_id`
- `created_at`

### 4.4 TaskRun

Suggested fields:

- `id`
- `task_id`
- `executor_actor_id`
- `status`
- `progress_percent`
- `lease_until`
- `started_at`
- `ended_at`
- `summary`

### 4.5 Submission

Suggested fields:

- `id`
- `task_run_id`
- `submitted_by_actor_id`
- `summary`
- `result_json`
- `review_status`
- `reviewed_by_actor_id`
- `reviewed_at`
- `created_at`

### 4.6 File

Use one unified file table for MVP.

Suggested fields:

- `id`
- `task_id`
- `run_id`
- `submission_id`
- `uploaded_by_actor_id`
- `kind`
- `original_name`
- `stored_name`
- `mime_type`
- `extension`
- `size_bytes`
- `storage_path`
- `sha256`
- `created_at`

### 4.7 Event

Tracks all task lifecycle changes.

Suggested fields:

- `id`
- `task_id`
- `run_id`
- `actor_id`
- `event_type`
- `payload_json`
- `created_at`

## 5. Authentication Plan

Use two entry methods that resolve to the same actor model:

- humans: session cookie after login
- agents: bearer API key

The business logic must not branch into separate task systems. Both authentication
flows must call the same domain services.

## 6. Initial API Surface

### 6.1 Human And Agent Shared APIs

- `POST /api/tasks`
- `GET /api/tasks`
- `GET /api/tasks/{task_id}`
- `POST /api/tasks/{task_id}/claim`
- `POST /api/tasks/{task_id}/progress`
- `POST /api/tasks/{task_id}/submit`
- `POST /api/tasks/{task_id}/approve`
- `POST /api/tasks/{task_id}/reject`
- `GET /api/files/{file_id}/download`

### 6.2 Actor API

- `GET /api/actors/me`

## 7. Web Page Plan

### 7.1 `/tasks`

Server-rendered task list with filters:

- status
- executor constraints
- reasoning tier
- browser requirement

### 7.2 `/tasks/{task_id}`

Task detail page with:

- metadata
- package file list
- event history
- submission file list
- review panel

### 7.3 `/tasks/new`

Form-based creation page using multipart upload.

### 7.4 `/actors`

Actor directory page for operational visibility.

## 8. Storage Plan

Start with a filesystem-backed storage service.

Recommended layout:

```text
data/
  files/
    YYYY/
      MM/
        DD/
          <file-id>-<sanitized-name>
```

Reasons:

- simple to implement
- avoids tightly coupling business logic to folder semantics
- easy to migrate to object storage later

## 9. Package Parsing Plan

Implement a package parser service that:

- validates `manifest.yaml`
- records metadata in the database
- extracts files into storage
- creates file metadata rows

Do not mix parsing logic into route handlers.

## 10. Development Status

### Completed

- draft the manifest contract
- create SQLAlchemy models
- ship the task creation, claim, progress, submit, and review flow
- add web pages and Agent API key support
- add Alembic migrations and health checks

### Suggested Next Steps

- tighten manifest schema validation and versioning
- add finer-grained login and permissions
- improve production PostgreSQL guidance
- extend operations visibility and task filtering

## 11. Local Development Workflow

Suggested local loop:

1. start PostgreSQL
2. run migrations: `alembic upgrade head`
3. start FastAPI in reload mode
4. upload an example task package
5. claim and submit through API
6. verify the task in the browser

Recommended commands:

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Operational endpoints:

- `GET /healthz`
- `GET /readyz`

## 12. VPS Deployment Notes

Recommended companion doc:

- `docs/DEPLOYMENT_LOCAL.zh-CN.md`

Recommended single-node deployment:

- FastAPI app container
- PostgreSQL container
- mounted persistent volume for `data/`

The reverse proxy is expected to live outside this repository. The Compose file
binds the application to `127.0.0.1:8000` on the VPS so an existing host Caddy
or Nginx can proxy to it.

Minimum initial deployment guidance:

- use HTTPS
- keep app port private behind the host reverse proxy
- back up PostgreSQL and file storage
- store secrets in environment variables, not in git
- keep `AUTO_INIT_DB=false` in production
- run `alembic upgrade head` before serving traffic

Minimal host Caddy example:

```caddyfile
tasks.example.com {
  encode gzip
  reverse_proxy 127.0.0.1:8000
}
```

## 13. Security Checklist

Minimum launch checklist:

- hash API keys
- require authentication for file download
- validate upload size and extension
- sanitize file names
- log all review decisions
- add rate limiting on public-facing endpoints

## 14. Testing Strategy

Must-have tests for MVP:

- manifest validation tests
- task state transition tests
- claim permission tests
- file upload and download tests
- submission review tests

## 15. Coding Rules

- keep route handlers thin
- put business logic in services
- use typed schemas for request and response bodies
- keep file storage behind an interface
- emit an event row for every important lifecycle change

## 16. Immediate Next Tasks

The next implementation work should be:

1. tighten `manifest.yaml` schema validation and package versioning
2. add finer login and permission controls
3. improve the production deployment handbook
4. expand operations visibility and task filtering
