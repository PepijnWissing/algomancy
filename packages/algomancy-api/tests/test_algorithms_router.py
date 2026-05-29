"""Algorithm + KPI discovery routes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from algomancy_api import ApiConfiguration, ApiLauncher


@pytest.fixture
def client(api_core_kwargs) -> TestClient:
    cfg = ApiConfiguration(use_sessions=False, **api_core_kwargs)
    return TestClient(ApiLauncher.build(cfg))


def test_list_algorithms_returns_configured_templates(client):
    r = client.get("/api/v1/sessions/main/algorithms")
    assert r.status_code == 200
    body = r.json()
    assert "Slow" in body["algorithms"]


def test_list_algorithms_unknown_session_returns_404(client):
    r = client.get("/api/v1/sessions/nope/algorithms")
    assert r.status_code == 404


def test_list_kpis_returns_configured_templates(client):
    r = client.get("/api/v1/sessions/main/kpis")
    assert r.status_code == 200
    assert "Delay" in r.json()["kpis"]


def test_get_algorithm_parameters_describes_each_field(client):
    r = client.get("/api/v1/sessions/main/algorithms/Slow/parameters")
    assert r.status_code == 200
    body = r.json()

    assert body["name"] == "Slow"
    assert isinstance(body["parameters"], list)

    # SlowAlgorithm has a single IntegerParameter("duration", min=1, max=60)
    by_name = {p["name"]: p for p in body["parameters"]}
    assert "duration" in by_name
    duration = by_name["duration"]
    assert duration["type"] == "integer"
    assert duration["required"] is True
    assert duration["min"] == 1
    assert duration["max"] == 60
    # value is the current parameter value (default 1 for IntegerParameter when unset)
    assert duration["value"] == 1
    assert duration["default"] == 1


def test_get_algorithm_parameters_unknown_algorithm_returns_404(client):
    r = client.get("/api/v1/sessions/main/algorithms/DoesNotExist/parameters")
    assert r.status_code == 404
    assert "DoesNotExist" in r.json()["detail"]


def test_get_algorithm_parameters_unknown_session_returns_404(client):
    r = client.get("/api/v1/sessions/nope/algorithms/Slow/parameters")
    assert r.status_code == 404


def test_openapi_includes_algorithm_routes(client):
    spec = client.get("/openapi.json").json()
    paths = set(spec["paths"].keys())
    assert "/api/v1/sessions/{session_id}/algorithms" in paths
    assert (
        "/api/v1/sessions/{session_id}/algorithms/{algorithm_name}/parameters" in paths
    )
    assert "/api/v1/sessions/{session_id}/kpis" in paths
