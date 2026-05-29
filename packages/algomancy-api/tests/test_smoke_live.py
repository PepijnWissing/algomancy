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

import os
import pathlib
import socket
import subprocess
import sys
import time

import httpx
import pytest


# Repo root — the example wiring uses ``example/data`` as a relative path, so
# the subprocess must run with cwd here for ``--example`` to resolve.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


def _find_free_port() -> int:
    """Bind ``0`` to grab an OS-assigned free port, then immediately release."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_health(
    base_url: str,
    timeout_seconds: float,
    proc: subprocess.Popen,
    log_path: pathlib.Path,
) -> None:
    """Poll ``/health`` until 200, or fail with the subprocess's logs if not.

    The example wiring runs ETL on every session on startup, which can take
    several seconds and generate a lot of log output. We redirect output to a
    file (so the pipes can't fill and block the process) and surface the file
    contents on any startup failure.
    """
    deadline = time.monotonic() + timeout_seconds
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            log_text = log_path.read_text(errors="replace") if log_path.exists() else ""
            pytest.fail(
                f"algomancy-api exited with code {proc.returncode} before "
                f"becoming healthy. Logs:\n{log_text}"
            )
        try:
            r = httpx.get(f"{base_url}/health", timeout=1.0)
            if r.status_code == 200:
                return
        except httpx.HTTPError as exc:
            last_err = exc
        time.sleep(0.25)
    log_text = log_path.read_text(errors="replace") if log_path.exists() else ""
    pytest.fail(
        f"algomancy-api did not respond on {base_url}/health within "
        f"{timeout_seconds}s; last error: {last_err}\nLogs:\n{log_text}"
    )


@pytest.fixture(scope="module")
def live_server(tmp_path_factory):
    """Module-scoped: start one ``algomancy-api --example`` and reuse it."""
    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    log_path = tmp_path_factory.mktemp("algomancy-api-smoke") / "server.log"

    # Use the same Python interpreter as the test runner so uv state, sys.path,
    # and the installed scripts all line up — invoking the console script by
    # name would also work but this is more robust on Windows.
    cmd = [
        sys.executable,
        "-m",
        "algomancy_api.main",
        "--example",
        "--port",
        str(port),
    ]
    env = os.environ.copy()

    log_file = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        cmd,
        cwd=str(REPO_ROOT),
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        # Example startup runs ETL on every session — give it generous time.
        _wait_for_health(base_url, timeout_seconds=60.0, proc=proc, log_path=log_path)
        yield base_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5.0)
        log_file.close()


# ---- Smoke tests ---------------------------------------------------------


def test_health_endpoint_responds(live_server):
    r = httpx.get(f"{live_server}/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["use_sessions"] is True
    # The example wiring discovers ``default_session`` and ``test_session`` on
    # disk; both must show up.
    assert "default_session" in body["sessions"]
    assert "test_session" in body["sessions"]


def test_sessions_endpoint_lists_example_sessions(live_server):
    r = httpx.get(f"{live_server}/api/v1/sessions")
    assert r.status_code == 200
    body = r.json()
    assert set(body["sessions"]) >= {"default_session", "test_session"}
    assert body["default"] in body["sessions"]


def test_algorithms_endpoint_exposes_example_algorithms(live_server):
    sessions = httpx.get(f"{live_server}/api/v1/sessions").json()
    sid = sessions["default"]
    r = httpx.get(f"{live_server}/api/v1/sessions/{sid}/algorithms")
    assert r.status_code == 200
    # The example wiring registers Slow, AsIs, Batching, Random.
    assert "Slow" in r.json()["algorithms"]


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
    assert "Slow" in algorithms

    data_keys = httpx.get(f"{live_server}/api/v1/sessions/{sid}/data").json()["keys"]
    assert data_keys, "example default_session is expected to ship with data"
    dataset_key = data_keys[0]

    # Create.
    create = httpx.post(
        f"{live_server}/api/v1/sessions/{sid}/scenarios",
        json={
            "tag": "smoke-e2e",
            "dataset_key": dataset_key,
            "algo_name": "Slow",
            "algo_params": {"duration": 1},
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
    any_kpi = next(iter(full["kpis"].values()))
    assert any_kpi["value"] is not None

    # Cleanup.
    delete = httpx.delete(
        f"{live_server}/api/v1/sessions/{sid}/scenarios/{sid_scenario}"
    )
    assert delete.status_code == 204
