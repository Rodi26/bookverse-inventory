import os
import sys
from pathlib import Path
from importlib import reload

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture()
def client(tmp_path, monkeypatch) -> TestClient:
    db_file = tmp_path / "test_inventory.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")

    import app.database as database
    import app.models as models
    reload(database)
    reload(models)
    database.create_all()

    from app.main import app
    test_client = TestClient(app)
    return test_client
