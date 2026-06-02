"""Sessions router: list, create, copy, rename."""

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


def _ids_by_display_name(client: TestClient) -> dict[str, str]:
    body = client.get("/api/v1/sessions").json()
    return {s["display_name"]: s["id"] for s in body["sessions"]}


def test_list_sessions_default_only(app_empty_sessions):
    client = TestClient(app_empty_sessions)
    r = client.get("/api/v1/sessions")
    assert r.status_code == 200
    body = r.json()
    assert len(body["sessions"]) == 1
    assert body["sessions"][0]["display_name"] == "main"
    assert body["sessions"][0]["id"] == body["default"]


def test_list_sessions_discovers_disk_sessions(app_sessions):
    client = TestClient(app_sessions)
    assert {"alpha", "beta"} <= _ids_by_display_name(client).keys()


def test_create_session_succeeds(app_sessions):
    client = TestClient(app_sessions)
    r = client.post("/api/v1/sessions", json={"display_name": "gamma"})
    assert r.status_code == 201
    names = {s["display_name"] for s in r.json()["sessions"]}
    assert "gamma" in names

    # Confirm round-trip via list.
    r2 = client.get("/api/v1/sessions")
    names2 = {s["display_name"] for s in r2.json()["sessions"]}
    assert "gamma" in names2


def test_create_session_rejects_duplicate_with_409(app_sessions):
    client = TestClient(app_sessions)
    r = client.post("/api/v1/sessions", json={"display_name": "alpha"})
    assert r.status_code == 409
    assert "alpha" in r.json()["detail"]


def test_create_session_accepts_strings_with_punctuation(app_sessions):
    """Display names are user-facing labels — slashes, dots, and spaces are all
    fine; the storage layer slugifies them safely."""
    client = TestClient(app_sessions)
    r = client.post("/api/v1/sessions", json={"display_name": "Alice's Run #1"})
    assert r.status_code == 201


def test_create_session_rejects_empty_name_with_422(app_sessions):
    """Pydantic-level validation rejects empty display_names with 422 before
    the route handler ever sees them."""
    client = TestClient(app_sessions)
    r = client.post("/api/v1/sessions", json={"display_name": ""})
    assert r.status_code == 422


def test_create_session_missing_body_is_422(app_sessions):
    client = TestClient(app_sessions)
    r = client.post("/api/v1/sessions", json={})
    assert r.status_code == 422


def test_copy_session_succeeds(app_sessions):
    client = TestClient(app_sessions)
    ids = _ids_by_display_name(client)
    r = client.post(
        f"/api/v1/sessions/{ids['alpha']}/copy",
        json={"new_display_name": "alpha-copy"},
    )
    assert r.status_code == 201
    names = {s["display_name"] for s in r.json()["sessions"]}
    assert "alpha-copy" in names


def test_copy_session_unknown_source_returns_404(app_sessions):
    client = TestClient(app_sessions)
    r = client.post(
        "/api/v1/sessions/does-not-exist/copy",
        json={"new_display_name": "irrelevant"},
    )
    assert r.status_code == 404
    assert "does-not-exist" in r.json()["detail"]


def test_copy_session_duplicate_destination_returns_409(app_sessions):
    client = TestClient(app_sessions)
    ids = _ids_by_display_name(client)
    r = client.post(
        f"/api/v1/sessions/{ids['alpha']}/copy",
        json={"new_display_name": "beta"},  # already exists from fixture
    )
    assert r.status_code == 409
    assert "beta" in r.json()["detail"]


def test_rename_session_updates_display_name(app_sessions):
    client = TestClient(app_sessions)
    ids = _ids_by_display_name(client)
    alpha_id = ids["alpha"]
    r = client.patch(
        f"/api/v1/sessions/{alpha_id}",
        json={"display_name": "alpha-renamed"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == alpha_id  # id is immutable
    assert body["display_name"] == "alpha-renamed"

    # List confirms the rename, and the id stayed the same.
    refreshed = _ids_by_display_name(client)
    assert "alpha" not in refreshed
    assert refreshed["alpha-renamed"] == alpha_id


def test_rename_session_unknown_id_returns_404(app_sessions):
    client = TestClient(app_sessions)
    r = client.patch(
        "/api/v1/sessions/does-not-exist",
        json={"display_name": "irrelevant"},
    )
    assert r.status_code == 404


def test_rename_session_duplicate_display_name_returns_409(app_sessions):
    client = TestClient(app_sessions)
    ids = _ids_by_display_name(client)
    r = client.patch(
        f"/api/v1/sessions/{ids['alpha']}",
        json={"display_name": "beta"},
    )
    assert r.status_code == 409


def test_openapi_lists_session_routes(app_sessions):
    client = TestClient(app_sessions)
    spec = client.get("/openapi.json").json()
    paths = set(spec["paths"].keys())
    assert "/api/v1/sessions" in paths
    assert "/api/v1/sessions/{session_id}/copy" in paths
    assert "/api/v1/sessions/{session_id}" in paths  # PATCH route
