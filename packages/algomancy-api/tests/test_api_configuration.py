import pytest

from algomancy_api import ApiConfiguration
from algomancy_scenario import CoreConfig


def test_defaults(api_core_kwargs):
    cfg = ApiConfiguration(**api_core_kwargs)
    assert isinstance(cfg, CoreConfig)
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 8051
    assert cfg.prefix == "/api/v1"
    assert cfg.cors_origins == []
    assert cfg.allow_session_create is True


def test_overrides(api_core_kwargs):
    cfg = ApiConfiguration(
        host="0.0.0.0",
        port=9000,
        prefix="/v2",
        cors_origins=["http://localhost:3000"],
        **api_core_kwargs,
    )
    assert cfg.host == "0.0.0.0"
    assert cfg.port == 9000
    assert cfg.prefix == "/v2"
    assert cfg.cors_origins == ["http://localhost:3000"]


def test_as_dict_includes_api_fields(api_core_kwargs):
    cfg = ApiConfiguration(port=8052, **api_core_kwargs)
    d = cfg.as_dict()
    # core fields preserved
    assert d["save_type"] == "json"
    # api fields present
    assert d["host"] == "127.0.0.1"
    assert d["port"] == 8052
    assert d["prefix"] == "/api/v1"
    assert d["cors_origins"] == []
    assert d["allow_session_create"] is True
    assert d["forwarded_allow_ips"] is None


def test_forwarded_allow_ips_accepts_string(api_core_kwargs):
    cfg = ApiConfiguration(forwarded_allow_ips="*", **api_core_kwargs)
    assert cfg.forwarded_allow_ips == "*"
    assert cfg.as_dict()["forwarded_allow_ips"] == "*"


def test_forwarded_allow_ips_accepts_list(api_core_kwargs):
    cfg = ApiConfiguration(
        forwarded_allow_ips=["10.0.0.1", "10.0.0.2"], **api_core_kwargs
    )
    assert cfg.forwarded_allow_ips == ["10.0.0.1", "10.0.0.2"]
    assert cfg.as_dict()["forwarded_allow_ips"] == ["10.0.0.1", "10.0.0.2"]


def test_allow_session_create_can_be_disabled(api_core_kwargs):
    cfg = ApiConfiguration(allow_session_create=False, **api_core_kwargs)
    assert cfg.allow_session_create is False
    assert cfg.as_dict()["allow_session_create"] is False


@pytest.mark.parametrize(
    "kwarg",
    [
        {"host": ""},
        {"host": 1},
        {"port": 0},
        {"port": 70000},
        {"port": "8051"},
        {"prefix": "v1"},  # missing leading slash
        {"prefix": 123},
        {"cors_origins": [""]},
        {"cors_origins": [42]},
        {"allow_session_create": "yes"},
        {"allow_session_create": None},
        {"forwarded_allow_ips": ""},
        {"forwarded_allow_ips": "  "},
        {"forwarded_allow_ips": []},
        {"forwarded_allow_ips": [""]},
        {"forwarded_allow_ips": [42]},
        {"forwarded_allow_ips": 42},
    ],
)
def test_invalid_api_fields_rejected(api_core_kwargs, kwarg):
    with pytest.raises(ValueError):
        ApiConfiguration(**{**api_core_kwargs, **kwarg})
