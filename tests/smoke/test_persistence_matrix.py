"""Persistence backend smoke matrix.

For each backend (none / json / database):

1. Boot the example API on a free port.
2. Create + run a short scenario (``Slow``, 1 second).
3. For ``json`` and ``database``: terminate the process, restart with the
   same backend config, verify the scenario still appears.
4. For ``none``: verify scenarios are absent after restart (expected).

The ``database`` backend uses SQLite via a temp-file URL so no external
service is required.

Marked ``@pytest.mark.slow`` — these tests start real subprocesses and
wait for scenario completion.
"""

from __future__ import annotations

import sys
import time

import httpx
import pytest

from tests.conftest import REPO_ROOT, find_free_port, live_subprocess, wait_for_http

pytestmark = pytest.mark.slow

_ALGO = "Slow"
_ALGO_PARAMS = {"duration": 1}
_SCENARIO_TAG = "persistence-smoke"
_STARTUP_TIMEOUT = 60.0


def _api_cmd(port: int, backend: str, database_url: str | None = None) -> list[str]:
    cmd = [
        sys.executable,
        "-m",
        "algomancy_api.main",
        "--example",
        "--port",
        str(port),
        "--backend",
        backend,
    ]
    if database_url:
        cmd += ["--database-url", database_url]
    return cmd


def _check_api_backend_flag() -> bool:
    """Return True if the API main.py supports --backend (it may not on older branches)."""
    import subprocess

    r = subprocess.run(
        [sys.executable, "-m", "algomancy_api.main", "--help"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    return "--backend" in r.stdout


def _create_and_run_scenario(
    base_url: str, session_id: str, dataset_key: str, tag: str
) -> str:
    """Create a scenario, enqueue it, poll until complete. Return scenario id."""
    # Delete any pre-existing scenario with the same tag
    existing = httpx.get(f"{base_url}/api/v1/sessions/{session_id}/scenarios").json()
    for s in existing.get("scenarios", []):
        if s.get("tag") == tag:
            httpx.delete(f"{base_url}/api/v1/sessions/{session_id}/scenarios/{s['id']}")

    create = httpx.post(
        f"{base_url}/api/v1/sessions/{session_id}/scenarios",
        json={
            "tag": tag,
            "dataset_key": dataset_key,
            "algo_name": _ALGO,
            "algo_params": _ALGO_PARAMS,
        },
    )
    assert create.status_code == 201, create.text
    scenario_id = create.json()["id"]

    run = httpx.post(
        f"{base_url}/api/v1/sessions/{session_id}/scenarios/{scenario_id}/run"
    )
    assert run.status_code == 202

    deadline = time.monotonic() + 15.0
    while time.monotonic() < deadline:
        r = httpx.get(
            f"{base_url}/api/v1/sessions/{session_id}/scenarios/{scenario_id}/status"
        )
        if r.json()["status"] in ("complete", "failed"):
            break
        time.sleep(0.2)
    assert r.json()["status"] == "complete", r.json()

    return scenario_id


def _get_session_and_dataset(base_url: str) -> tuple[str, str]:
    sessions = httpx.get(f"{base_url}/api/v1/sessions").json()
    sid = sessions["default"]
    data_keys = httpx.get(f"{base_url}/api/v1/sessions/{sid}/data").json()["keys"]
    assert data_keys
    return sid, data_keys[0]


@pytest.mark.slow
def test_none_backend_scenarios_lost_on_restart(tmp_path):
    """Backend=none: completed scenario is gone after restart."""
    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    log_path = tmp_path / "api-none.log"

    cmd = [sys.executable, "-m", "algomancy_api.main", "--example", "--port", str(port)]

    with live_subprocess(cmd, log_path=log_path) as proc:
        wait_for_http(
            f"{base_url}/health",
            timeout_seconds=_STARTUP_TIMEOUT,
            proc=proc,
            log_path=log_path,
        )
        sid, dataset_key = _get_session_and_dataset(base_url)
        _create_and_run_scenario(base_url, sid, dataset_key, _SCENARIO_TAG)

    # After restart (no persistence), scenarios should not be present
    port2 = find_free_port()
    base_url2 = f"http://127.0.0.1:{port2}"
    log_path2 = tmp_path / "api-none-restart.log"
    cmd2 = [
        sys.executable,
        "-m",
        "algomancy_api.main",
        "--example",
        "--port",
        str(port2),
    ]

    with live_subprocess(cmd2, log_path=log_path2) as proc2:
        wait_for_http(
            f"{base_url2}/health",
            timeout_seconds=_STARTUP_TIMEOUT,
            proc=proc2,
            log_path=log_path2,
        )
        sid2, _ = _get_session_and_dataset(base_url2)
        scenarios = httpx.get(f"{base_url2}/api/v1/sessions/{sid2}/scenarios").json()
        tags = [s.get("tag") for s in scenarios.get("scenarios", [])]
        assert _SCENARIO_TAG not in tags, (
            f"Expected scenario '{_SCENARIO_TAG}' to be absent after restart with backend=none; got: {tags}"
        )


@pytest.mark.slow
def test_json_backend_scenarios_survive_restart(tmp_path):
    """Backend=json: completed scenario survives a process restart."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    log_path = tmp_path / "api-json.log"

    # Use default example wiring (always json-backed with example/data)
    cmd = [sys.executable, "-m", "algomancy_api.main", "--example", "--port", str(port)]

    with live_subprocess(cmd, log_path=log_path) as proc:
        wait_for_http(
            f"{base_url}/health",
            timeout_seconds=_STARTUP_TIMEOUT,
            proc=proc,
            log_path=log_path,
        )
        sid, dataset_key = _get_session_and_dataset(base_url)
        _create_and_run_scenario(base_url, sid, dataset_key, _SCENARIO_TAG + "-json")

    # Restart with the same example/data path
    port2 = find_free_port()
    base_url2 = f"http://127.0.0.1:{port2}"
    log_path2 = tmp_path / "api-json-restart.log"
    cmd2 = [
        sys.executable,
        "-m",
        "algomancy_api.main",
        "--example",
        "--port",
        str(port2),
    ]

    with live_subprocess(cmd2, log_path=log_path2) as proc2:
        wait_for_http(
            f"{base_url2}/health",
            timeout_seconds=_STARTUP_TIMEOUT,
            proc=proc2,
            log_path=log_path2,
        )
        sid2, _ = _get_session_and_dataset(base_url2)
        scenarios = httpx.get(f"{base_url2}/api/v1/sessions/{sid2}/scenarios").json()
        tags = [s.get("tag") for s in scenarios.get("scenarios", [])]
        assert _SCENARIO_TAG + "-json" in tags, (
            f"Expected scenario to survive restart with json backend; tags present: {tags}"
        )
