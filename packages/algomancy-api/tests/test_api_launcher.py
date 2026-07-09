import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from algomancy_api import ApiConfiguration, ApiLauncher


@pytest.fixture
def app(api_core_kwargs) -> FastAPI:
    cfg = ApiConfiguration(**api_core_kwargs)
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
    display_names = [
        s["display_name"] for s in app.state.session_manager.list_sessions()
    ]
    assert "main" in display_names


def test_build_accepts_dict(api_core_kwargs):
    app = ApiLauncher.build({**api_core_kwargs})
    assert isinstance(app, FastAPI)


def test_build_accepts_core_config(api_core_kwargs):
    from algomancy_scenario import CoreConfig

    cfg = CoreConfig(**api_core_kwargs)
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
    display_names = [s["display_name"] for s in body["sessions"]]
    assert "main" in display_names
    assert "use_sessions" not in body


def test_openapi_docs_available(client: TestClient):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert r.json()["info"]["title"] == "Algomancy API"


def test_cors_middleware_active_when_origins_configured(api_core_kwargs):
    cfg = ApiConfiguration(
        cors_origins=["http://example.com"],
        **api_core_kwargs,
    )
    app = ApiLauncher.build(cfg)
    client = TestClient(app)
    r = client.get("/health", headers={"Origin": "http://example.com"})
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "http://example.com"


def _add_echo_scheme_route(app: FastAPI) -> None:
    from fastapi import Request

    @app.get("/_test/echo-scheme")
    def echo_scheme(request: Request) -> dict:
        return {"scheme": request.url.scheme, "client": request.client.host}


def test_forwarded_proto_ignored_by_default(api_core_kwargs):
    cfg = ApiConfiguration(**api_core_kwargs)
    app = ApiLauncher.build(cfg)
    _add_echo_scheme_route(app)
    client = TestClient(app)
    r = client.get("/_test/echo-scheme", headers={"X-Forwarded-Proto": "https"})
    assert r.status_code == 200
    # Without forwarded_allow_ips configured, the proxy header must not be trusted.
    assert r.json()["scheme"] == "http"


def test_forwarded_proto_honored_when_configured(api_core_kwargs):
    cfg = ApiConfiguration(forwarded_allow_ips="*", **api_core_kwargs)
    app = ApiLauncher.build(cfg)
    _add_echo_scheme_route(app)
    client = TestClient(app)
    r = client.get(
        "/_test/echo-scheme",
        headers={"X-Forwarded-Proto": "https", "X-Forwarded-For": "203.0.113.42"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["scheme"] == "https"
    assert body["client"] == "203.0.113.42"


def test_forwarded_proto_ignored_when_client_not_in_trusted_list(api_core_kwargs):
    # TestClient's synthetic client is 'testclient' (not an IP); restricting the
    # trusted list to a specific IP must cause the proxy header to be ignored.
    cfg = ApiConfiguration(forwarded_allow_ips="10.0.0.1", **api_core_kwargs)
    app = ApiLauncher.build(cfg)
    _add_echo_scheme_route(app)
    client = TestClient(app)
    r = client.get("/_test/echo-scheme", headers={"X-Forwarded-Proto": "https"})
    assert r.status_code == 200
    assert r.json()["scheme"] == "http"
