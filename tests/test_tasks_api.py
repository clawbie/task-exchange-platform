def test_create_task_via_json_and_list_it(client):
    payload = {
        "title": "Write product notes",
        "description": "Summarize the product discussion into clear notes.",
        "creator_name": "clawbie",
        "creator_type": "human",
        "executor_constraints": "human_or_agent",
        "reasoning_tier": "medium",
        "browser_requirement": "none",
        "compute_requirement": "tiny",
        "speed_priority": "balanced",
        "deliverables": ["summary.md", "result.json"],
        "acceptance": ["Must include action items", "Keep wording concise"],
    }

    create_response = client.post("/api/tasks", json=payload)

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["title"] == payload["title"]
    assert created["status"] == "published"
    assert created["created_by_actor"]["name"] == "clawbie"
    assert created["deliverables"] == payload["deliverables"]
    assert created["acceptance"] == payload["acceptance"]

    task_id = created["id"]

    list_response = client.get("/api/tasks")
    assert list_response.status_code == 200
    listed_tasks = list_response.json()
    assert any(task["id"] == task_id for task in listed_tasks)

    detail_response = client.get(f"/api/tasks/{task_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == task_id


def test_create_task_with_attachments_and_download_file(client):
    form_data = {
        "title": "Collect source files",
        "description": "Store task inputs with uploaded files.",
        "creator_name": "openclaw-bot",
        "creator_type": "agent",
        "executor_constraints": "agent_only",
        "reasoning_tier": "low",
        "browser_requirement": "none",
        "compute_requirement": "tiny",
        "speed_priority": "fast",
        "deliverables": "report.md\nartifacts.zip",
        "acceptance": "Must keep all uploaded files",
    }
    files = [
        ("attachments", ("brief.md", b"# Brief\n\nTask context", "text/markdown")),
        ("attachments", ("input.csv", b"id,value\n1,42\n", "text/csv")),
    ]

    response = client.post("/api/tasks/upload", data=form_data, files=files)

    assert response.status_code == 201
    created = response.json()
    assert created["created_by_actor"]["type"] == "agent"
    assert len(created["files"]) == 2
    assert {item["original_name"] for item in created["files"]} == {"brief.md", "input.csv"}

    first_file_id = created["files"][0]["id"]
    download_response = client.get(f"/api/files/{first_file_id}/download")

    assert download_response.status_code == 200
    assert download_response.headers["content-disposition"]
    assert download_response.content


def test_list_actors_after_task_creation(client):
    create_response = client.post(
        "/api/tasks",
        json={
            "title": "Seed actor list",
            "description": "Create a task so the creator actor exists.",
            "creator_name": "reviewer-01",
            "creator_type": "service",
            "executor_constraints": "human_or_agent",
            "reasoning_tier": "high",
            "browser_requirement": "read_only",
            "compute_requirement": "small",
            "speed_priority": "quality",
            "deliverables": ["actor-list.txt"],
            "acceptance": ["Actor should appear in actor list"],
        },
    )

    assert create_response.status_code == 201

    actors_response = client.get("/api/actors")

    assert actors_response.status_code == 200
    actors = actors_response.json()
    assert len(actors) == 1
    assert actors[0]["name"] == "reviewer-01"
    assert actors[0]["type"] == "service"


def test_create_task_from_manifest_file(client):
    response = client.post(
        "/api/tasks/upload",
        data={},
        files=[
            (
                "manifest_file",
                (
                    "manifest.yaml",
                    b"""
title: Manifest-created task
description: Loaded from manifest
creator_name: manifest-bot
creator_type: agent
executor_constraints: agent_only
reasoning_tier: high
browser_requirement: read_only
compute_requirement: small
speed_priority: quality
deliverables:
  - report.md
acceptance:
  - Must come from manifest
""",
                    "application/x-yaml",
                ),
            ),
        ],
    )

    assert response.status_code == 201
    created = response.json()
    assert created["title"] == "Manifest-created task"
    assert created["created_by_actor"]["name"] == "manifest-bot"
    assert created["executor_constraints"] == "agent_only"


def test_reject_incomplete_agent_task_payload(client):
    response = client.post(
        "/api/tasks",
        json={
            "title": "Bad agent task",
            "creator_name": "agent-x",
            "creator_type": "agent",
            "executor_constraints": "agent_only",
        },
    )

    assert response.status_code == 422


def test_allow_minimal_human_task_payload(client):
    response = client.post(
        "/api/tasks",
        json={
            "title": "Minimal human task",
            "creator_type": "human",
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["title"] == "Minimal human task"
