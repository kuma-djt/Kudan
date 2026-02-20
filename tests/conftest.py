from __future__ import annotations

import os

os.environ["KUDAN_DB_PATH"] = "/tmp/kudan_test.sqlite"

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app


@pytest.fixture(autouse=True)
def setup_db() -> None:
    if os.path.exists("/tmp/kudan_test.sqlite"):
        os.remove("/tmp/kudan_test.sqlite")
    db.init_db()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
