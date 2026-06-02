"""Tests for error handlers + the get_scenario_manager dependency.

We mount probe routes that raise each exception type and assert the HTTP status
code mapping. Routes use the real dependency to verify session 404s.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from algomancy_api import ApiConfiguration, ApiLauncher
from algomancy_api.dependencies import get_scenario_manager


@pytest.fixture
def app(api_core_kwargs) -> FastAPI:
    cfg = ApiConfiguration(**api_core_kwargs)
    app = ApiLauncher.build(cfg)

    @app.get("/probe/value")
    def _value():
        raise ValueError("bad input")

    @app.get("/probe/key")
    def _key():
        raise KeyError("missing thing")

    @app.get("/probe/assert")
    def _assert():
        assert False, "precondition broken"

    @app.get("/probe/boom")
    def _boom():
        raise RuntimeError("unexpected")

    @app.get("/probe/session/{session_id}")
    def _session(sm=Depends(get_scenario_manager)):
        return {"ok": True, "data_keys": sm.get_data_keys()}

    return app


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_value_error_maps_to_400(client):
    r = client.get("/probe/value")
    assert r.status_code == 400
    assert r.json()["detail"] == "bad input"


def test_key_error_not_globally_translated(client):
    """A KeyError raised in route code should NOT be silently turned into 404 —
    only explicit lookups translate it (see dependencies.get_scenario_manager).
    A stray KeyError surfaces as 500 so real bugs are not hidden behind a 404."""
    r = client.get("/probe/key")
    assert r.status_code == 500
    assert r.json()["detail"] == "Internal server error"


def test_assertion_error_maps_to_409(client):
    r = client.get("/probe/assert")
    assert r.status_code == 409
    # Python 3.14 appends the failing expression to AssertionError's str(),
    # so substring-match the human-supplied message.
    assert "precondition broken" in r.json()["detail"]


def test_unexpected_error_maps_to_500(client):
    r = client.get("/probe/boom")
    assert r.status_code == 500
    assert r.json()["detail"] == "Internal server error"


def test_get_scenario_manager_resolves_existing(client):
    r = client.get("/probe/session/main")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_get_scenario_manager_404_on_unknown_session(client):
    r = client.get("/probe/session/does-not-exist")
    assert r.status_code == 404
    assert "does-not-exist" in r.json()["detail"]
