"""Scenarios router: CRUD + run + poll + processing.

Includes an end-to-end test: create -> run -> poll until COMPLETE -> verify
KPI was computed -> delete.
"""

from __future__ import annotations

import pathlib
import shutil
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from algomancy_api import ApiConfiguration, ApiLauncher


# A real dataset key — loaded into the SessionManager by debug_load_data below.
DATASET_KEY = "example_data"

# Path to the example data shipped with the algomancy-scenario test fixtures.
_EXAMPLE_DATA_SRC = (
    pathlib.Path(__file__).resolve().parents[2]
    / "algomancy-scenario"
    / "tests"
    / "data"
    / "example_data"
)


@pytest.fixture
def client(api_core_kwargs, tmp_path) -> TestClient:
    """A TestClient backed by a ScenarioManager with one dataset loaded.

    Copies the bundled example data into the test's tmp_path so the Slow
    algorithm has a real dataset to operate on and each test stays isolated.
    """
    # The SessionManager creates a per-session subfolder (here ``main/``)
    # under data_path on construction, and the ScenarioManager's data folder is
    # that subfolder. Place the example data inside it so debug_load_data finds
    # it via os.path.join(session_path, DATASET_KEY).
    main_dir = tmp_path / "main"
    main_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(_EXAMPLE_DATA_SRC, main_dir / DATASET_KEY)

    kwargs = dict(api_core_kwargs)
    kwargs["data_path"] = str(tmp_path)
    cfg = ApiConfiguration(**kwargs)
    app: FastAPI = ApiLauncher.build(cfg)

    sm = app.state.session_manager.get_scenario_manager("main")
    sm.debug_load_data(DATASET_KEY)
    return TestClient(app)


# ---- List / create -------------------------------------------------------


def test_list_scenarios_starts_empty(client):
    r = client.get("/api/v1/sessions/main/scenarios")
    assert r.status_code == 200
    assert r.json() == []


def test_create_scenario_succeeds(client):
    r = client.post(
        "/api/v1/sessions/main/scenarios",
        json={
            "tag": "fast",
            "dataset_key": DATASET_KEY,
            "algo_name": "Slow",
            "algo_params": {"duration": 1},
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["tag"] == "fast"
    assert "id" in body
    assert body["status"] == "created"
    assert body["result"] is None


def test_create_scenario_default_params(client):
    r = client.post(
        "/api/v1/sessions/main/scenarios",
        json={
            "tag": "defaults",
            "dataset_key": DATASET_KEY,
            "algo_name": "Slow",
            # algo_params omitted -> defaults
        },
    )
    assert r.status_code == 201


def test_create_scenario_unknown_algorithm_returns_404(client):
    r = client.post(
        "/api/v1/sessions/main/scenarios",
        json={
            "tag": "x",
            "dataset_key": DATASET_KEY,
            "algo_name": "DoesNotExist",
            "algo_params": {},
        },
    )
    assert r.status_code == 404
    assert "DoesNotExist" in r.json()["detail"]


def test_create_scenario_unknown_dataset_returns_404(client):
    r = client.post(
        "/api/v1/sessions/main/scenarios",
        json={
            "tag": "x",
            "dataset_key": "no-such-dataset",
            "algo_name": "Slow",
            "algo_params": {},
        },
    )
    assert r.status_code == 404
    assert "no-such-dataset" in r.json()["detail"]


def test_create_scenario_duplicate_tag_returns_409(client):
    payload = {
        "tag": "dup",
        "dataset_key": DATASET_KEY,
        "algo_name": "Slow",
        "algo_params": {"duration": 1},
    }
    r1 = client.post("/api/v1/sessions/main/scenarios", json=payload)
    assert r1.status_code == 201
    r2 = client.post("/api/v1/sessions/main/scenarios", json=payload)
    assert r2.status_code == 409
    assert "dup" in r2.json()["detail"]


def test_create_scenario_bad_params_returns_400(client):
    r = client.post(
        "/api/v1/sessions/main/scenarios",
        json={
            "tag": "bad",
            "dataset_key": DATASET_KEY,
            "algo_name": "Slow",
            # duration is constrained to 1..60; 999 violates the upper bound
            "algo_params": {"duration": 999},
        },
    )
    assert r.status_code == 400


def test_create_scenario_missing_required_field_returns_422(client):
    r = client.post(
        "/api/v1/sessions/main/scenarios",
        json={"tag": "x"},  # missing dataset_key + algo_name
    )
    assert r.status_code == 422


# ---- Get / delete --------------------------------------------------------


def test_get_scenario_by_id(client):
    create = client.post(
        "/api/v1/sessions/main/scenarios",
        json={
            "tag": "getme",
            "dataset_key": DATASET_KEY,
            "algo_name": "Slow",
            "algo_params": {"duration": 1},
        },
    ).json()
    r = client.get(f"/api/v1/sessions/main/scenarios/{create['id']}")
    assert r.status_code == 200
    assert r.json()["tag"] == "getme"


def test_get_scenario_unknown_id_returns_404(client):
    r = client.get("/api/v1/sessions/main/scenarios/nope")
    assert r.status_code == 404


def test_delete_scenario(client):
    create = client.post(
        "/api/v1/sessions/main/scenarios",
        json={
            "tag": "to-delete",
            "dataset_key": DATASET_KEY,
            "algo_name": "Slow",
            "algo_params": {"duration": 1},
        },
    ).json()
    sid = create["id"]

    r = client.delete(f"/api/v1/sessions/main/scenarios/{sid}")
    assert r.status_code == 204

    # Subsequent get -> 404
    r = client.get(f"/api/v1/sessions/main/scenarios/{sid}")
    assert r.status_code == 404


def test_delete_scenario_unknown_id_returns_404(client):
    r = client.delete("/api/v1/sessions/main/scenarios/nope")
    assert r.status_code == 404


# ---- Run / poll / processing --------------------------------------------


def _poll_until_terminal(
    client: TestClient,
    session: str,
    scenario_id: str,
    timeout_seconds: float = 5.0,
) -> dict:
    """Poll the lightweight status endpoint until the scenario reaches a
    terminal state, then return the status body. Fails the test on timeout."""
    deadline = time.monotonic() + timeout_seconds
    last = None
    while time.monotonic() < deadline:
        r = client.get(f"/api/v1/sessions/{session}/scenarios/{scenario_id}/status")
        assert r.status_code == 200
        last = r.json()
        if last["status"] in ("complete", "failed"):
            return last
        time.sleep(0.05)
    pytest.fail(f"Scenario did not reach a terminal state in time: last={last}")


def test_run_then_poll_to_completion(client):
    create = client.post(
        "/api/v1/sessions/main/scenarios",
        json={
            "tag": "run-and-poll",
            "dataset_key": DATASET_KEY,
            "algo_name": "Slow",
            "algo_params": {"duration": 1},
        },
    ).json()
    sid = create["id"]

    # Enqueue.
    r = client.post(f"/api/v1/sessions/main/scenarios/{sid}/run")
    assert r.status_code == 202
    body = r.json()
    assert body["status"] in ("queued", "processing", "complete")

    # Poll until done.
    final = _poll_until_terminal(client, "main", sid)
    assert final["status"] == "complete"
    assert final["progress"] == 100.0

    # The full scenario endpoint includes the computed KPI now.
    full = client.get(f"/api/v1/sessions/main/scenarios/{sid}").json()
    assert full["status"] == "complete"
    assert "Delay" in full["kpis"]
    assert full["kpis"]["Delay"]["value"] is not None


def test_run_unknown_scenario_returns_404(client):
    r = client.post("/api/v1/sessions/main/scenarios/nope/run")
    assert r.status_code == 404


def test_currently_processing_when_idle(client):
    r = client.get("/api/v1/sessions/main/processing")
    assert r.status_code == 200
    assert r.json() is None


def test_status_endpoint_shape(client):
    create = client.post(
        "/api/v1/sessions/main/scenarios",
        json={
            "tag": "status-shape",
            "dataset_key": DATASET_KEY,
            "algo_name": "Slow",
            "algo_params": {"duration": 1},
        },
    ).json()
    r = client.get(f"/api/v1/sessions/main/scenarios/{create['id']}/status")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"id", "tag", "status", "progress"}
    assert body["id"] == create["id"]
    assert body["tag"] == "status-shape"
    assert body["status"] == "created"
    assert body["progress"] == 0.0


# ---- Cross-resource ------------------------------------------------------


def test_list_scenarios_reflects_creates_and_deletes(client):
    initial = client.get("/api/v1/sessions/main/scenarios").json()
    assert initial == []

    for tag in ("a", "b", "c"):
        client.post(
            "/api/v1/sessions/main/scenarios",
            json={
                "tag": tag,
                "dataset_key": DATASET_KEY,
                "algo_name": "Slow",
                "algo_params": {"duration": 1},
            },
        )

    listed = client.get("/api/v1/sessions/main/scenarios").json()
    assert {s["tag"] for s in listed} == {"a", "b", "c"}

    # Delete one and confirm.
    sid_a = next(s["id"] for s in listed if s["tag"] == "a")
    client.delete(f"/api/v1/sessions/main/scenarios/{sid_a}")
    listed2 = client.get("/api/v1/sessions/main/scenarios").json()
    assert {s["tag"] for s in listed2} == {"b", "c"}


def test_unknown_session_for_scenario_routes_returns_404(client):
    r = client.get("/api/v1/sessions/nope/scenarios")
    assert r.status_code == 404


def test_openapi_lists_scenario_routes(client):
    spec = client.get("/openapi.json").json()
    paths = set(spec["paths"].keys())
    assert "/api/v1/sessions/{session_id}/scenarios" in paths
    assert "/api/v1/sessions/{session_id}/scenarios/{scenario_id}" in paths
    assert "/api/v1/sessions/{session_id}/scenarios/{scenario_id}/run" in paths
    assert "/api/v1/sessions/{session_id}/scenarios/{scenario_id}/status" in paths
    assert "/api/v1/sessions/{session_id}/processing" in paths
