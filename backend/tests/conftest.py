import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET"] = "test-secret-only"

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.models import User
from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _headers_for(client: TestClient, account: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login", json={"account": account, "password": password}
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def auth_headers(client):
    return _headers_for(client, "demo@gongxue.local", "demo12345")


@pytest.fixture(scope="session")
def admin_headers(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "测试审核员",
            "email": "reviewer@test.local",
            "password": "reviewer12345",
        },
    )
    assert response.status_code in {200, 201}
    with SessionLocal() as db:
        reviewer = db.query(User).filter(User.email == "reviewer@test.local").one()
        reviewer.role = "admin"
        db.commit()
    return _headers_for(client, "reviewer@test.local", "reviewer12345")
