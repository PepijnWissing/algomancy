"""Sessions router: list, create, copy."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from algomancy_api import ApiConfiguration, ApiLauncher


@pytest.fixture
def app_empty_sessions(api_core_kwargs, tmp_path) -> FastAPI:
    """SessionManager scoped to an empty data folder — auto-creates 'main'."""
    kwargs = dict(api_core_kwargs)
    kwargs["data_path"] = str(tmp_path)
    cfg = ApiConfiguration(**kwargs)
    return ApiLauncher.build(cfg)


@pytest.fixture
def app_sessions(api_core_kwargs, tmp_path) -> FastAPI:
    # Pre-seed two session directories so list_sessions has something to enumerate
    # beyond the default.
    (tmp_path / "alpha").mkdir(exist_ok=True)
    (tmp_path / "beta").mkdir(exist_ok=True)
    kwargs = dict(api_core_kwargs)
    kwargs["data_path"] = str(tmp_path)
    cfg = ApiConfiguration(**kwargs)
    return ApiLauncher.build(cfg)


def test_list_sessions_default_only(app_empty_sessions):
    client = TestClient(app_empty_sessions)
    r = client.get("/api/v1/sessions")
    assert r.status_code == 200
    body = r.json()
    assert body["sessions"] == ["main"]
    assert body["default"] == "main"


def test_list_sessions_discovers_disk_sessions(app_sessions):
    client = TestClient(app_sessions)
    r = client.get("/api/v1/sessions")
    assert r.status_code == 200
    assert set(r.json()["sessions"]) == {"alpha", "beta"}


def test_create_session_succeeds(app_sessions):
    client = TestClient(app_sessions)
    r = client.post("/api/v1/sessions", json={"name": "gamma"})
    assert r.status_code == 201
    assert "gamma" in r.json()["sessions"]

    # Confirm round-trip via list.
    r2 = client.get("/api/v1/sessions")
    assert "gamma" in r2.json()["sessions"]


def test_create_session_rejects_duplicate_with_409(app_sessions):
    client = TestClient(app_sessions)
    r = client.post("/api/v1/sessions", json={"name": "alpha"})
    assert r.status_code == 409
    assert "alpha" in r.json()["detail"]


@pytest.mark.parametrize(
    "bad_name",
    ["../escape", "foo/bar", "..", ".", "C:abc"],
)
def test_create_session_rejects_unsafe_names_with_409(app_sessions, bad_name):
    client = TestClient(app_sessions)
    r = client.post("/api/v1/sessions", json={"name": bad_name})
    assert r.status_code == 409
    assert "detail" in r.json()


def test_create_session_rejects_empty_name_with_422(app_sessions):
    """Pydantic-level validation rejects empty names with 422 before the route
    handler ever sees them."""
    client = TestClient(app_sessions)
    r = client.post("/api/v1/sessions", json={"name": ""})
    assert r.status_code == 422


def test_create_session_missing_body_is_422(app_sessions):
    client = TestClient(app_sessions)
    r = client.post("/api/v1/sessions", json={})
    assert r.status_code == 422


def test_copy_session_succeeds(app_sessions):
    client = TestClient(app_sessions)
    r = client.post(
        "/api/v1/sessions/alpha/copy",
        json={"new_name": "alpha-copy"},
    )
    assert r.status_code == 201
    assert "alpha-copy" in r.json()["sessions"]


def test_copy_session_unknown_source_returns_404(app_sessions):
    client = TestClient(app_sessions)
    r = client.post(
        "/api/v1/sessions/does-not-exist/copy",
        json={"new_name": "irrelevant"},
    )
    assert r.status_code == 404
    assert "does-not-exist" in r.json()["detail"]


def test_copy_session_duplicate_destination_returns_409(app_sessions):
    client = TestClient(app_sessions)
    r = client.post(
        "/api/v1/sessions/alpha/copy",
        json={"new_name": "beta"},  # already exists from fixture
    )
    assert r.status_code == 409
    assert "beta" in r.json()["detail"]


def test_copy_session_unsafe_destination_returns_409(app_sessions):
    client = TestClient(app_sessions)
    r = client.post(
        "/api/v1/sessions/alpha/copy",
        json={"new_name": "../escape"},
    )
    assert r.status_code == 409


def test_openapi_lists_session_routes(app_sessions):
    client = TestClient(app_sessions)
    spec = client.get("/openapi.json").json()
    paths = set(spec["paths"].keys())
    assert "/api/v1/sessions" in paths
    assert "/api/v1/sessions/{session_id}/copy" in paths
