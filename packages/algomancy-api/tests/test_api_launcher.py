import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from algomancy_api import ApiConfiguration, ApiLauncher


@pytest.fixture
def app(api_core_kwargs) -> FastAPI:
    cfg = ApiConfiguration(use_sessions=False, **api_core_kwargs)
    return ApiLauncher.build(cfg)


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def test_build_returns_fastapi(app):
    assert isinstance(app, FastAPI)


def test_build_attaches_state(app):
    assert app.state.config is not None
    assert app.state.session_manager is not None
    # default session always exists
    assert "main" in app.state.session_manager.sessions_names


def test_build_accepts_dict(api_core_kwargs):
    app = ApiLauncher.build({"use_sessions": False, **api_core_kwargs})
    assert isinstance(app, FastAPI)


def test_build_accepts_core_config(api_core_kwargs):
    from algomancy_scenario import CoreConfig

    cfg = CoreConfig(use_sessions=False, **api_core_kwargs)
    app = ApiLauncher.build(cfg)
    assert isinstance(app, FastAPI)


def test_build_rejects_garbage():
    with pytest.raises(TypeError):
        ApiLauncher.build(object())


def test_health_endpoint(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["title"] == "Algomancy API"
    assert "main" in body["sessions"]
    assert body["use_sessions"] is False


def test_openapi_docs_available(client: TestClient):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert r.json()["info"]["title"] == "Algomancy API"


def test_cors_middleware_active_when_origins_configured(api_core_kwargs):
    cfg = ApiConfiguration(
        use_sessions=False,
        cors_origins=["http://example.com"],
        **api_core_kwargs,
    )
    app = ApiLauncher.build(cfg)
    client = TestClient(app)
    r = client.get("/health", headers={"Origin": "http://example.com"})
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "http://example.com"
