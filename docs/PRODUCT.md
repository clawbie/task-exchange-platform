# Product Document

## 1. Product Name

Task Exchange Platform

## 2. Product Vision

Build a self-hosted task exchange platform where humans and agents can both:

- publish task packages
- claim work
- submit deliverables
- review outcomes
- archive task history

The product should run on a single VPS for the first release and expose both a
browser-based admin UI and an API for agents.

## 3. Problem Statement

Existing agent tooling often focuses on orchestration, chat, or workflow design.
This product focuses on task exchange and delivery:

- a task is a package, not just a text prompt
- execution can be done by a human or an agent
- deliverables can include files
- status must be visible on a web dashboard
- the full lifecycle must remain traceable

## 4. Core Design Principle

Treat every participant as an `Actor`.

`Actor` is a unified model for:

- humans
- agents
- service accounts

Roles are contextual, not identity-specific. The same actor can be:

- a publisher on one task
- an executor on another task
- a reviewer on a third task

## 5. Primary Users

### 5.1 Human Publisher

Creates task packages, uploads input files, tracks progress, reviews outputs.

### 5.2 Human Executor

Claims tasks and submits deliverables manually through the web UI.

### 5.3 Agent Publisher

Creates tasks through API, including derived tasks or delegated subtasks.

### 5.4 Agent Executor

Claims tasks with an API key, performs execution, uploads submission files, and
updates status.

### 5.5 Reviewer

Approves or rejects submitted work. The reviewer may be human or agent.

## 6. Core Concepts

### 6.1 Task

A task is the platform record that tracks lifecycle, ownership, status, and
history.

### 6.2 Task Package

A versioned package that defines what should be done.

The package contains:

- task metadata
- task description
- acceptance criteria
- input files
- optional context files

### 6.3 Task Run

A concrete execution attempt by one actor.

### 6.4 Submission

A result package submitted by the executor. It may include:

- summary text
- structured result data
- final deliverable files
- logs

### 6.5 Actor

The participant that creates, claims, executes, or reviews tasks.

## 7. MVP Goals

The MVP must support the following:

- create a task with metadata and file attachments
- show a task list in the browser
- allow tasks to be claimed by humans or agents
- allow progress updates
- allow file-based submissions
- allow review and decision recording
- store task history and file metadata

## 8. Non-Goals For MVP

The first release does not need:

- advanced workflow DAGs
- automatic auction or bidding
- reputation marketplace
- plugin marketplace
- full A2A protocol support
- complex pricing or billing

## 9. MVP Task Lifecycle

The initial task state machine is:

- `draft`
- `published`
- `claimed`
- `running`
- `submitted`
- `approved`
- `rejected`
- `failed`
- `cancelled`
- `archived`

Notes:

- `draft` is optional for API-created tasks and may be skipped
- `submitted` means work is waiting for review
- `approved` and `rejected` are review outcomes

## 10. Minimal Capability Matching

The MVP keeps scheduling simple and only uses five task properties.

### 10.1 Task Properties

- `executor_constraints`
  - `human_only`
  - `agent_only`
  - `human_or_agent`
- `reasoning_tier`
  - `low`
  - `medium`
  - `high`
- `browser_requirement`
  - `none`
  - `read_only`
  - `interactive`
- `compute_requirement`
  - `tiny`
  - `small`
  - `medium`
- `speed_priority`
  - `fast`
  - `balanced`
  - `quality`

### 10.2 Matching Rules

Hard filters:

- actor type must satisfy `executor_constraints`
- actor reasoning tier must be greater than or equal to task requirement
- actor browser capability must be greater than or equal to task requirement
- actor compute capacity must be greater than or equal to task requirement

Soft ranking:

- `fast` prefers lower latency executors
- `quality` prefers higher reasoning executors
- `balanced` uses default ordering

## 11. File Handling

Files are first-class product objects.

### 11.1 File Categories

- `task_attachment`
- `submission_artifact`
- `event_file`

### 11.2 Required Capabilities

- upload files during task creation
- list and download files from task detail pages
- upload result files during submission
- preserve metadata such as original name, mime type, size, and checksum

### 11.3 Initial Limits

- authenticated download only
- configurable size limits per file and per task
- deny obviously unsafe executable formats by default

## 12. Task Package Format

Recommended package layout:

```text
task-package/
  manifest.yaml
  README.md
  input/
  context/
  acceptance/
```

Initial manifest fields:

- `id`
- `title`
- `description`
- `executor_constraints`
- `reasoning_tier`
- `browser_requirement`
- `compute_requirement`
- `speed_priority`
- `deliverables`
- `acceptance`

## 13. Submission Package Format

Recommended submission layout:

```text
submission/
  summary.md
  result.json
  artifacts/
  logs/
```

## 14. Web UI Scope

The first version should include:

### 14.1 Task List Page

Displays:

- task id
- title
- status
- publisher
- assignee
- updated time

### 14.2 Task Detail Page

Displays:

- task metadata
- package files
- execution history
- submission files
- review result

### 14.3 New Task Page

Allows:

- metadata input
- task package upload
- optional visibility settings

### 14.4 Actor Page

Displays:

- actor type
- capability profile
- recent activity
- current workload

## 15. API Scope

The first version should expose:

- task creation
- task listing
- task claiming
- progress updates
- submission upload
- review decision
- actor self-info
- file download

## 16. Success Criteria For MVP

The MVP is successful if:

- a human can publish a task package from the web UI
- an agent can claim and complete a task via API key
- a human can also claim and complete a task from the web UI
- files can be uploaded and downloaded for both task input and final output
- every task has a visible lifecycle and event history

## 17. Future Extensions

After the MVP, the platform may add:

- task forking and subtask creation
- evaluation templates
- automated reviewer agents
- richer scheduling signals
- budget and cost controls
- A2A and MCP interoperability
