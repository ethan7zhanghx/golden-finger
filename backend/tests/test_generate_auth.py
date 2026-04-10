"""Unit tests verifying that /generate and related AI endpoints require authentication (BUG-02)."""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    "method, path",
    [
        ("POST", "/api/projects/test-proj/steps/worldview/generate"),
        ("POST", "/api/projects/test-proj/steps/worldview/rewrite"),
        ("GET", "/api/projects/test-proj/steps/worldview/context"),
    ],
)
def test_ai_endpoints_require_auth(method: str, path: str):
    """Unauthenticated requests must receive 401 Unauthorized."""
    response = client.request(method, path, json={})
    assert response.status_code == 401, (
        f"{method} {path} should return 401 for unauthenticated requests, got {response.status_code}"
    )
