"""End-to-end smoke test against a live ``algomancy-api --example`` process.

Unlike the other test modules (which use ``fastapi.testclient.TestClient`` and
talk to the app in-process), this test:

1. Launches the real ``algomancy-api`` console script in a subprocess so the
   uvicorn server actually binds a port and serves HTTP.
2. Drives it with ``httpx`` against ``http://127.0.0.1:<free port>``.
3. Walks through the canonical client flow: list sessions → list algorithms →
   create scenario → run → poll until complete → fetch full result.
4. Verifies the OpenAPI docs render.
5. Terminates the subprocess cleanly in teardown.

If startup fails (port already in use, example wiring broken, ...) we capture
stderr from the subprocess and surface it so the failure is debuggable.
"""

from __future__ import annotations

import sys
import time

import httpx
import pytest

from algomancy_utils._smoke_helpers import (
    find_free_port,
    live_subprocess,
    wait_for_http,
)


@pytest.fixture(scope="module")
def live_server(tmp_path_factory):
    """Module-scoped: start one ``algomancy-api --example`` and reuse it."""
    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    log_path = tmp_path_factory.mktemp("algomancy-api-smoke") / "server.log"

    cmd = [
        sys.executable,
        "-m",
        "algomancy_api.main",
        "--example",
        "--port",
        str(port),
    ]

    with live_subprocess(cmd, log_path=log_path) as proc:
        # Example startup runs ETL on every session — give it generous time.
        wait_for_http(
            f"{base_url}/health",
            timeout_seconds=60.0,
            proc=proc,
            log_path=log_path,
        )
        yield base_url


# ---- Smoke tests ---------------------------------------------------------


def test_health_endpoint_responds(live_server):
    r = httpx.get(f"{live_server}/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    # The example wiring ships a single ``default_session`` on disk.
    # Multi-session discovery semantics are unit-tested in
    # packages/algomancy-scenario/tests/test_session_manager.py.
    assert "default_session" in body["sessions"]


def test_sessions_endpoint_lists_example_sessions(live_server):
    r = httpx.get(f"{live_server}/api/v1/sessions")
    assert r.status_code == 200
    body = r.json()
    assert "default_session" in body["sessions"]
    assert body["default"] in body["sessions"]


def test_algorithms_endpoint_exposes_example_algorithms(live_server):
    sessions = httpx.get(f"{live_server}/api/v1/sessions").json()
    sid = sessions["default"]
    r = httpx.get(f"{live_server}/api/v1/sessions/{sid}/algorithms")
    assert r.status_code == 200
    # The example registry must expose the warehouse-slotting algorithms.
    assert "Instant" in r.json()["algorithms"]


def test_openapi_docs_and_schema_available(live_server):
    spec = httpx.get(f"{live_server}/openapi.json")
    assert spec.status_code == 200
    paths = set(spec.json()["paths"].keys())
    # A few canonical routes from each router.
    for expected in [
        "/health",
        "/api/v1/sessions",
        "/api/v1/sessions/{session_id}/algorithms",
        "/api/v1/sessions/{session_id}/scenarios",
        "/api/v1/sessions/{session_id}/data",
    ]:
        assert expected in paths, f"missing route in OpenAPI spec: {expected}"

    docs = httpx.get(f"{live_server}/docs")
    assert docs.status_code == 200
    assert "swagger" in docs.text.lower()


def test_end_to_end_create_run_complete(live_server):
    """The flagship plan-spec smoke: create scenario → run → poll until COMPLETE
    → verify KPIs computed → delete."""
    sessions = httpx.get(f"{live_server}/api/v1/sessions").json()
    sid = sessions["default"]

    # Pick an algorithm + dataset that we know exist in the example.
    algorithms = httpx.get(f"{live_server}/api/v1/sessions/{sid}/algorithms").json()[
        "algorithms"
    ]
    assert "Instant" in algorithms

    data_keys = httpx.get(f"{live_server}/api/v1/sessions/{sid}/data").json()["keys"]
    assert data_keys, "example default_session is expected to ship with data"
    dataset_key = data_keys[0]

    # Create.
    create = httpx.post(
        f"{live_server}/api/v1/sessions/{sid}/scenarios",
        json={
            "tag": "smoke-e2e",
            "dataset_key": dataset_key,
            "algo_name": "Instant",
            "algo_params": {},
        },
    )
    assert create.status_code == 201, create.text
    sid_scenario = create.json()["id"]

    # Run.
    run = httpx.post(
        f"{live_server}/api/v1/sessions/{sid}/scenarios/{sid_scenario}/run"
    )
    assert run.status_code == 202

    # Poll the lightweight status endpoint until terminal.
    deadline = time.monotonic() + 10.0
    final = None
    while time.monotonic() < deadline:
        r = httpx.get(
            f"{live_server}/api/v1/sessions/{sid}/scenarios/{sid_scenario}/status"
        )
        assert r.status_code == 200
        final = r.json()
        if final["status"] in ("complete", "failed"):
            break
        time.sleep(0.1)
    assert final is not None and final["status"] == "complete", final

    # Full scenario response should carry KPI values now.
    full = httpx.get(
        f"{live_server}/api/v1/sessions/{sid}/scenarios/{sid_scenario}"
    ).json()
    assert full["status"] == "complete"
    assert full["kpis"], "expected at least one KPI in completed scenario"
    # Some registered KPIs intentionally return NaN/Inf (which serialise to
    # null) or are type-guarded against non-warehouse results. Require AT
    # LEAST one KPI to have produced a usable numeric value.
    assert any(k["value"] is not None for k in full["kpis"].values()), (
        f"No KPI produced a numeric value: {full['kpis']}"
    )

    # Cleanup.
    delete = httpx.delete(
        f"{live_server}/api/v1/sessions/{sid}/scenarios/{sid_scenario}"
    )
    assert delete.status_code == 204
