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
    ],
)
def test_invalid_api_fields_rejected(api_core_kwargs, kwarg):
    with pytest.raises(ValueError):
        ApiConfiguration(**{**api_core_kwargs, **kwarg})
