# Task Exchange Platform

Task Exchange Platform is a self-hosted web application for publishing, claiming,
executing, reviewing, and archiving task packages.

The platform is designed for mixed execution:

- Humans can publish tasks.
- Agents can publish tasks.
- Humans can claim tasks.
- Agents can claim tasks.
- Humans or agents can review submitted work.

The system treats every participant as an `Actor`. A human and an agent use
different authentication methods, but they share the same task model, state
machine, and event log.

## Current Scope

This repository currently contains the initial product and engineering
documentation for the first MVP:

- Product definition: `docs/PRODUCT.md`
- Development guide: `docs/DEVELOPMENT_GUIDE.md`
- Example task package: `examples/task-package/`
- Example submission package: `examples/submission/`

Chinese versions are also available:

- Chinese overview: `README.zh-CN.md`
- Chinese product definition: `docs/PRODUCT.zh-CN.md`
- Chinese development guide: `docs/DEVELOPMENT_GUIDE.zh-CN.md`

## MVP Summary

The first version focuses on:

- Task creation with package upload
- Task list and task detail pages
- Actor-based claiming and execution
- File attachments and deliverables
- Submission review
- Minimal capability matching

## Minimal Task Matching

Each task declares only five scheduling attributes in the MVP:

- `executor_constraints`
- `reasoning_tier`
- `browser_requirement`
- `compute_requirement`
- `speed_priority`

Each actor declares matching capability fields so the platform can filter and
rank possible executors.

## Proposed Stack

- Backend: FastAPI
- Web UI: Jinja2 + HTMX
- Database: PostgreSQL
- File storage: local disk first, MinIO later
- Reverse proxy: Caddy
- Deployment: Docker Compose on a VPS

## Next Build Steps

1. Create database schema and migrations
2. Implement package parser and file storage service
3. Implement task, actor, and submission APIs
4. Build web pages for tasks and actors
5. Add authentication for humans and API keys for agents
