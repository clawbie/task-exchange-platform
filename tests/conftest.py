import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    database_path = tmp_path / "test.db"
    storage_root = tmp_path / "files"

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path.as_posix()}")
    monkeypatch.setenv("STORAGE_ROOT", str(storage_root))
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("AUTO_INIT_DB", "true")

    from app.config import get_settings

    get_settings.cache_clear()

    import app.db as db_module
    import app.deps as deps_module
    import app.main as main_module
    import app.routes.api_actors as api_actors_module
    import app.routes.api_files as api_files_module
    import app.routes.api_tasks as api_tasks_module
    import app.routes.web as web_module
    import app.services.tasks as tasks_service_module

    importlib.reload(db_module)
    importlib.reload(deps_module)
    importlib.reload(tasks_service_module)
    importlib.reload(api_tasks_module)
    importlib.reload(api_files_module)
    importlib.reload(api_actors_module)
    importlib.reload(web_module)
    main_module = importlib.reload(main_module)

    with TestClient(main_module.app) as test_client:
        yield test_client

    get_settings.cache_clear()
