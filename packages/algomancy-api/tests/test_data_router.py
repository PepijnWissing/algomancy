"""Data router: list / get / delete / derive / from-json / etl upload."""

from __future__ import annotations

import gc
import json
import pathlib
import shutil
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from algomancy_api import ApiConfiguration, ApiLauncher


DATASET_KEY = "example_data"
_EXAMPLE_DATA_SRC = (
    pathlib.Path(__file__).resolve().parents[2]
    / "algomancy-scenario"
    / "tests"
    / "data"
    / "example_data"
)


@pytest.fixture
def isolated_data_path():
    """A per-test data folder we clean up ourselves with ``ignore_errors=True``.

    pytest's ``tmp_path`` will hard-fail teardown on Windows when pandas/
    openpyxl hold a file handle on inventory.xlsx for an extra moment after
    the test body returns. We sidestep that by managing the temp dir manually.
    """
    base = pathlib.Path(tempfile.mkdtemp(prefix="algomancy-api-test-"))
    try:
        yield base
    finally:
        # Encourage release of any pandas/openpyxl handles before unlink.
        gc.collect()
        shutil.rmtree(base, ignore_errors=True)


def _stage_example_data(base: pathlib.Path) -> None:
    main_dir = base / "main"
    main_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(_EXAMPLE_DATA_SRC, main_dir / DATASET_KEY)


@pytest.fixture
def client_with_data(api_core_kwargs, isolated_data_path) -> TestClient:
    """Client where the example dataset is loaded into the default session."""
    _stage_example_data(isolated_data_path)
    kwargs = dict(api_core_kwargs)
    kwargs["data_path"] = str(isolated_data_path)
    cfg = ApiConfiguration(**kwargs)
    app: FastAPI = ApiLauncher.build(cfg)
    sm = app.state.session_manager.get_scenario_manager("main")
    sm.debug_load_data(DATASET_KEY)
    return TestClient(app)


@pytest.fixture
def client_empty(api_core_kwargs, isolated_data_path) -> TestClient:
    """Client with no data loaded — useful for ETL upload tests."""
    kwargs = dict(api_core_kwargs)
    kwargs["data_path"] = str(isolated_data_path)
    cfg = ApiConfiguration(**kwargs)
    return TestClient(ApiLauncher.build(cfg))


# ---- List / get -----------------------------------------------------------


def test_list_data_with_loaded_dataset(client_with_data):
    r = client_with_data.get("/api/v1/sessions/main/data")
    assert r.status_code == 200
    assert DATASET_KEY in r.json()["keys"]


def test_list_data_empty(client_empty):
    r = client_empty.get("/api/v1/sessions/main/data")
    assert r.status_code == 200
    assert r.json() == {"keys": []}


def test_get_data_returns_parsed_json(client_with_data):
    r = client_with_data.get(f"/api/v1/sessions/main/data/{DATASET_KEY}")
    assert r.status_code == 200
    body = r.json()
    # DataSource.to_json round-trip — at minimum a dict with some structure
    assert isinstance(body, dict)
    assert body  # non-empty


def test_get_data_unknown_returns_404(client_with_data):
    r = client_with_data.get("/api/v1/sessions/main/data/nope")
    assert r.status_code == 404
    assert "nope" in r.json()["detail"]


def test_get_data_parameters_returns_descriptor(client_with_data):
    """Plain ``DataSource`` declares no params — the endpoint still returns 200
    with an empty parameter list."""
    r = client_with_data.get(f"/api/v1/sessions/main/data/{DATASET_KEY}/parameters")
    assert r.status_code == 200
    body = r.json()
    assert "name" in body
    assert body["parameters"] == []


def test_get_data_parameters_unknown_returns_404(client_with_data):
    r = client_with_data.get("/api/v1/sessions/main/data/nope/parameters")
    assert r.status_code == 404


# ---- Delete ---------------------------------------------------------------


def test_delete_data_succeeds(client_with_data):
    # Delete a derived (non-master) dataset rather than the example master data:
    # ``DataManager.delete_data`` shells out to ``shutil.rmtree`` for master
    # data, and on Windows the xlsx files in example_data linger as locked by
    # openpyxl for a few hundred ms after load — a framework-level wart we
    # don't want to exercise from API tests.
    client_with_data.post(
        f"/api/v1/sessions/main/data/{DATASET_KEY}/derive",
        json={"new_key": "for_deletion"},
    )
    r = client_with_data.delete("/api/v1/sessions/main/data/for_deletion")
    assert r.status_code == 204
    assert (
        "for_deletion"
        not in client_with_data.get("/api/v1/sessions/main/data").json()["keys"]
    )


def test_delete_data_unknown_returns_404(client_with_data):
    r = client_with_data.delete("/api/v1/sessions/main/data/nope")
    assert r.status_code == 404


def test_delete_data_used_by_scenario_returns_409(client_with_data):
    """ScenarioManager asserts the dataset isn't referenced before deleting;
    that AssertionError must surface as a 409 conflict."""
    # Create a scenario that holds the dataset open.
    client_with_data.post(
        "/api/v1/sessions/main/scenarios",
        json={
            "tag": "uses-data",
            "dataset_key": DATASET_KEY,
            "algo_name": "Slow",
            "algo_params": {"duration": 1},
        },
    )
    r = client_with_data.delete(f"/api/v1/sessions/main/data/{DATASET_KEY}")
    assert r.status_code == 409


# ---- Derive ---------------------------------------------------------------


def test_derive_data_creates_new_key(client_with_data):
    r = client_with_data.post(
        f"/api/v1/sessions/main/data/{DATASET_KEY}/derive",
        json={"new_key": "derived_one"},
    )
    assert r.status_code == 201
    keys = r.json()["keys"]
    assert DATASET_KEY in keys
    assert "derived_one" in keys


def test_derive_data_unknown_source_returns_404(client_with_data):
    r = client_with_data.post(
        "/api/v1/sessions/main/data/nope/derive",
        json={"new_key": "anything"},
    )
    assert r.status_code == 404


def test_derive_data_duplicate_target_returns_409(client_with_data):
    # Use existing key as the destination.
    r = client_with_data.post(
        f"/api/v1/sessions/main/data/{DATASET_KEY}/derive",
        json={"new_key": DATASET_KEY},
    )
    assert r.status_code == 409


# ---- from-json -----------------------------------------------------------


def test_add_data_from_json_round_trip(client_with_data):
    # Round-trip: GET the existing dataset's JSON, POST it back under a new key.
    # DataSource.from_json keys the new datasource by ``metadata.name``, so we
    # rename that field — not the top-level — to avoid a duplicate key.
    src = client_with_data.get(f"/api/v1/sessions/main/data/{DATASET_KEY}").json()
    src["metadata"]["name"] = "from_json_clone"
    r = client_with_data.post(
        "/api/v1/sessions/main/data/from-json",
        content=json.dumps(src),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 201
    assert "from_json_clone" in r.json()["keys"]


def test_add_data_from_json_empty_body_returns_400(client_with_data):
    r = client_with_data.post(
        "/api/v1/sessions/main/data/from-json",
        content=b"",
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 400


def test_add_data_from_json_invalid_returns_400(client_with_data):
    r = client_with_data.post(
        "/api/v1/sessions/main/data/from-json",
        content=b"not-valid-json",
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 400


# ---- ETL multipart upload ------------------------------------------------


def _open_example_files():
    """Yield (filename, file-handle, content-type) tuples for the example
    dataset's source files. Used by the multipart ETL test."""
    src = _EXAMPLE_DATA_SRC
    paths = [
        ("sku_data.csv", src / "sku_data.csv", "text/csv"),
        ("warehouse_layout.csv", src / "warehouse_layout.csv", "text/csv"),
        ("employees.json", src / "employees.json", "application/json"),
        (
            "inventory.xlsx",
            src / "inventory.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        (
            "multisheet.xlsx",
            src / "multisheet.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
    ]
    return [(fn, p.read_bytes(), ct) for fn, p, ct in paths]


def test_etl_upload_creates_dataset(client_empty):
    files = [("files", (fn, content, ct)) for fn, content, ct in _open_example_files()]
    r = client_empty.post(
        "/api/v1/sessions/main/etl",
        data={"dataset_name": "uploaded"},
        files=files,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["dataset_name"] == "uploaded"
    assert body["success"] is True
    assert "uploaded" in body["keys"]


def test_etl_upload_rejects_unsupported_extension(client_empty):
    r = client_empty.post(
        "/api/v1/sessions/main/etl",
        data={"dataset_name": "x"},
        files=[("files", ("foo.txt", b"hello", "text/plain"))],
    )
    assert r.status_code == 400
    assert ".txt" in r.json()["detail"]


def test_etl_upload_missing_dataset_name_returns_422(client_empty):
    r = client_empty.post(
        "/api/v1/sessions/main/etl",
        files=[("files", ("foo.csv", b"a,b\n1,2\n", "text/csv"))],
    )
    assert r.status_code == 422


# ---- Cross-cutting --------------------------------------------------------


def test_unknown_session_for_data_routes_returns_404(client_with_data):
    r = client_with_data.get("/api/v1/sessions/nope/data")
    assert r.status_code == 404


def test_openapi_includes_data_routes(client_with_data):
    spec = client_with_data.get("/openapi.json").json()
    paths = set(spec["paths"].keys())
    assert "/api/v1/sessions/{session_id}/data" in paths
    assert "/api/v1/sessions/{session_id}/data/{data_key}" in paths
    assert "/api/v1/sessions/{session_id}/data/{data_key}/derive" in paths
    assert "/api/v1/sessions/{session_id}/data/from-json" in paths
    assert "/api/v1/sessions/{session_id}/etl" in paths
