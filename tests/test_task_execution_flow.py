import json


def _create_api_key(client, actor_name: str, actor_type: str = "agent") -> str:
    response = client.post(
        "/api/actors/api-keys",
        json={
            "actor_name": actor_name,
            "actor_type": actor_type,
            "label": "test-key",
        },
    )
    assert response.status_code == 200
    return response.json()["api_key"]


def test_api_key_auth_and_full_task_execution_flow(client):
    create_task_response = client.post(
        "/api/tasks",
        json={
            "title": "Execute review flow",
            "description": "Run through claim, progress, submit and review.",
            "creator_name": "planner",
            "creator_type": "human",
            "executor_constraints": "human_or_agent",
            "reasoning_tier": "medium",
            "browser_requirement": "none",
            "compute_requirement": "tiny",
            "speed_priority": "balanced",
            "deliverables": ["report.md"],
            "acceptance": ["Must complete full lifecycle"],
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    executor_key = _create_api_key(client, "executor-bot", "agent")
    reviewer_key = _create_api_key(client, "reviewer-bot", "service")

    me_response = client.get("/api/actors/me", headers={"Authorization": f"Bearer {executor_key}"})
    assert me_response.status_code == 200
    assert me_response.json()["name"] == "executor-bot"

    claim_response = client.post(f"/api/tasks/{task_id}/claim", headers={"Authorization": f"Bearer {executor_key}"})
    assert claim_response.status_code == 200
    assert claim_response.json()["status"] == "claimed"

    progress_response = client.post(
        f"/api/tasks/{task_id}/progress",
        headers={"Authorization": f"Bearer {executor_key}"},
        json={"progress_percent": 60, "summary": "Halfway done"},
    )
    assert progress_response.status_code == 200
    assert progress_response.json()["status"] == "running"
    assert progress_response.json()["progress_percent"] == 60

    submit_response = client.post(
        f"/api/tasks/{task_id}/submit",
        headers={"Authorization": f"Bearer {executor_key}"},
        data={
            "summary": "Execution completed",
            "result_json": json.dumps({"quality": "good", "items": 1}),
        },
        files=[
            ("artifacts", ("report.md", b"# Final report\n\nDone.", "text/markdown")),
        ],
    )
    assert submit_response.status_code == 200
    submitted = submit_response.json()
    assert submitted["review_status"] == "pending"
    assert len(submitted["files"]) == 1
    assert submitted["files"][0]["original_name"] == "report.md"

    closed_progress_response = client.post(
        f"/api/tasks/{task_id}/progress",
        headers={"Authorization": f"Bearer {executor_key}"},
        json={"progress_percent": 100, "summary": "Final marker"},
    )
    assert closed_progress_response.status_code == 409
    assert "progress updates are closed" in closed_progress_response.json()["detail"]

    review_response = client.post(
        f"/api/tasks/{task_id}/approve",
        headers={"Authorization": f"Bearer {reviewer_key}"},
        json={"comment": "Looks good"},
    )
    assert review_response.status_code == 200
    assert review_response.json()["review_status"] == "approved"

    detail_response = client.get(f"/api/tasks/{task_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["status"] == "approved"

    reopen_response = client.post(
        f"/api/tasks/{task_id}/reopen",
        headers={"Authorization": f"Bearer {reviewer_key}"},
        json={"comment": "Need another execution round"},
    )
    assert reopen_response.status_code == 200
    assert reopen_response.json()["status"] == "published"

    submissions_response = client.get(f"/api/tasks/{task_id}/submissions")
    assert submissions_response.status_code == 200
    submissions = submissions_response.json()
    assert len(submissions) == 1
    assert submissions[0]["review_status"] == "approved"


def test_claim_requires_api_key(client):
    create_task_response = client.post(
        "/api/tasks",
        json={
            "title": "Protected task",
            "description": "Should require auth for claim.",
            "executor_constraints": "human_or_agent",
            "reasoning_tier": "low",
            "browser_requirement": "none",
            "compute_requirement": "tiny",
            "speed_priority": "fast",
            "deliverables": [],
            "acceptance": [],
        },
    )
    task_id = create_task_response.json()["id"]

    response = client.post(f"/api/tasks/{task_id}/claim")

    assert response.status_code == 401


def test_only_service_can_review_task(client):
    create_task_response = client.post(
        "/api/tasks",
        json={
            "title": "Review permission task",
            "description": "Only service actors should review.",
            "creator_name": "planner",
            "creator_type": "human",
            "executor_constraints": "human_or_agent",
            "reasoning_tier": "medium",
            "browser_requirement": "none",
            "compute_requirement": "tiny",
            "speed_priority": "balanced",
            "deliverables": ["report.md"],
            "acceptance": ["Must complete full lifecycle"],
        },
    )
    task_id = create_task_response.json()["id"]

    executor_key = _create_api_key(client, "executor-a", "agent")
    human_reviewer_key = _create_api_key(client, "human-reviewer", "human")

    client.post(f"/api/tasks/{task_id}/claim", headers={"Authorization": f"Bearer {executor_key}"})
    client.post(
        f"/api/tasks/{task_id}/submit",
        headers={"Authorization": f"Bearer {executor_key}"},
        data={"summary": "done", "result_json": json.dumps({"ok": True})},
        files=[("artifacts", ("report.md", b"done", "text/markdown"))],
    )

    review_response = client.post(
        f"/api/tasks/{task_id}/approve",
        headers={"Authorization": f"Bearer {human_reviewer_key}"},
        json={"comment": "human review"},
    )
    assert review_response.status_code == 403


def test_human_cannot_claim_agent_only_task(client):
    create_task_response = client.post(
        "/api/tasks",
        json={
            "title": "Agent only task",
            "description": "Should reject human claims.",
            "executor_constraints": "agent_only",
            "reasoning_tier": "low",
            "browser_requirement": "none",
            "compute_requirement": "tiny",
            "speed_priority": "fast",
            "deliverables": [],
            "acceptance": [],
        },
    )
    task_id = create_task_response.json()["id"]
    human_key = _create_api_key(client, "human-reviewer", "human")

    response = client.post(f"/api/tasks/{task_id}/claim", headers={"Authorization": f"Bearer {human_key}"})

    assert response.status_code == 403
