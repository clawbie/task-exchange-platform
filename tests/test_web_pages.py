def test_web_task_flow_renders_pages(client):
    list_page = client.get("/tasks")
    assert list_page.status_code == 200
    assert "任务列表" in list_page.text
    assert "参与者" in list_page.text

    create_response = client.post(
        "/tasks/new",
        data={
            "title": "Create UI-visible task",
            "description": "This task should appear on the HTML pages.",
            "creator_name": "page-owner",
            "creator_type": "human",
            "executor_constraints": "human_or_agent",
            "reasoning_tier": "medium",
            "browser_requirement": "none",
            "compute_requirement": "tiny",
            "speed_priority": "balanced",
            "deliverables": "summary.md\nreport.md",
            "acceptance": "Visible on detail page\nVisible on actors page",
        },
        files=[
            ("attachments", ("notes.txt", b"page test attachment", "text/plain")),
        ],
        follow_redirects=False,
    )

    assert create_response.status_code == 303
    detail_url = create_response.headers["location"]
    assert detail_url.startswith("/tasks/task-")

    detail_page = client.get(detail_url)
    assert detail_page.status_code == 200
    assert "Create UI-visible task" in detail_page.text
    assert "notes.txt" in detail_page.text
    assert "summary.md" in detail_page.text
    assert "Visible on detail page" in detail_page.text

    actors_page = client.get("/actors")
    assert actors_page.status_code == 200
    assert "page-owner" in actors_page.text


def test_web_create_task_from_manifest_file(client):
    create_response = client.post(
        "/tasks/new",
        data={"creator_name": "override-owner"},
        files=[
            (
                "manifest_file",
                (
                    "manifest.yaml",
                    b"""
title: Web manifest task
description: Created from the web form manifest.
creator_name: manifest-web-bot
creator_type: agent
executor_constraints: agent_only
reasoning_tier: high
browser_requirement: read_only
compute_requirement: small
speed_priority: quality
deliverables:
  - report.md
acceptance:
  - Uses manifest values
""",
                    "application/x-yaml",
                ),
            )
        ],
        follow_redirects=False,
    )

    assert create_response.status_code == 303
    detail_page = client.get(create_response.headers["location"])
    assert detail_page.status_code == 200
    assert "Web manifest task" in detail_page.text
    assert "override-owner" in detail_page.text
    assert "agent_only" in detail_page.text
    assert "report.md" in detail_page.text


def test_web_claim_submit_and_review_flow(client):
    create_response = client.post(
        "/tasks/new",
        data={
            "title": "Web action flow task",
            "description": "Drive the flow from the task detail page.",
            "creator_name": "web-planner",
            "creator_type": "human",
            "executor_constraints": "human_or_agent",
            "reasoning_tier": "medium",
            "browser_requirement": "none",
            "compute_requirement": "tiny",
            "speed_priority": "balanced",
            "deliverables": "summary.md",
            "acceptance": "Can be approved from web",
        },
        follow_redirects=False,
    )
    task_url = create_response.headers["location"]

    claim_response = client.post(
        f"{task_url}/claim",
        data={"actor_name": "web-executor", "actor_type": "human"},
        follow_redirects=False,
    )
    assert claim_response.status_code == 303

    progress_response = client.post(
        f"{task_url}/progress",
        data={
            "actor_name": "web-executor",
            "actor_type": "human",
            "progress_percent": "75",
            "summary": "Almost done",
        },
        follow_redirects=False,
    )
    assert progress_response.status_code == 303

    submit_response = client.post(
        f"{task_url}/submit",
        data={
            "actor_name": "web-executor",
            "actor_type": "human",
            "summary": "Finished from web",
            "result_json": '{"channel": "web"}',
        },
        files=[("artifacts", ("summary.md", b"web summary", "text/markdown"))],
        follow_redirects=False,
    )
    assert submit_response.status_code == 303

    approve_response = client.post(
        f"{task_url}/approve",
        data={"actor_name": "web-reviewer", "actor_type": "service", "comment": "Approved from web"},
        follow_redirects=False,
    )
    assert approve_response.status_code == 303

    detail_page = client.get(task_url)
    assert detail_page.status_code == 200
    assert "submission_artifact" not in detail_page.text
    assert "summary.md" in detail_page.text
    assert "approved" in detail_page.text
