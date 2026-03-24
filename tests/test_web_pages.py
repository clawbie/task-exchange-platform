def test_web_task_flow_renders_pages(client):
    list_page = client.get("/tasks")
    assert list_page.status_code == 200
    assert "任务列表" in list_page.text

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
