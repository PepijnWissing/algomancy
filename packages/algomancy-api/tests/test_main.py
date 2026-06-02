"""CLI entry point: argparse, --config-callback, --example, and main()."""

from __future__ import annotations

import sys
import types

import pytest

from algomancy_api import ApiConfiguration
from algomancy_api.main import (
    _load_config_from_callback,
    _parse_args,
    build_example_config,
    main,
)


# ---- argparse -------------------------------------------------------------


def test_parse_args_callback_only():
    ns = _parse_args(["--config-callback", "pkg:fn"])
    assert ns.config_callback == "pkg:fn"
    assert ns.example is False
    assert ns.host is None
    assert ns.port is None


def test_parse_args_example_with_overrides():
    ns = _parse_args(["--example", "--host", "0.0.0.0", "--port", "9001"])
    assert ns.example is True
    assert ns.host == "0.0.0.0"
    assert ns.port == 9001


# ---- _load_config_from_callback ------------------------------------------


def _install_fake_module(name: str, attrs: dict) -> None:
    """Register a synthetic module so importlib can find it."""
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[name] = mod


def test_load_config_from_callback_returns_api_configuration(api_core_kwargs):
    def make_config() -> ApiConfiguration:
        return ApiConfiguration(**api_core_kwargs)

    _install_fake_module("_test_api_callback_ok", {"make_config": make_config})
    try:
        cfg = _load_config_from_callback("_test_api_callback_ok:make_config")
        assert isinstance(cfg, ApiConfiguration)
    finally:
        sys.modules.pop("_test_api_callback_ok", None)


def test_load_config_from_callback_rejects_missing_colon():
    with pytest.raises(ValueError, match="module:function"):
        _load_config_from_callback("just_a_module_name")


def test_load_config_from_callback_rejects_wrong_return_type():
    def make_garbage():
        return {"not": "an api configuration"}

    _install_fake_module("_test_api_callback_wrong", {"make_garbage": make_garbage})
    try:
        with pytest.raises(TypeError, match="ApiConfiguration"):
            _load_config_from_callback("_test_api_callback_wrong:make_garbage")
    finally:
        sys.modules.pop("_test_api_callback_wrong", None)


def test_load_config_from_callback_unknown_module():
    with pytest.raises(ModuleNotFoundError):
        _load_config_from_callback("definitely_not_a_module:fn")


def test_load_config_from_callback_unknown_function():
    _install_fake_module("_test_api_callback_attr", {})
    try:
        with pytest.raises(AttributeError):
            _load_config_from_callback("_test_api_callback_attr:does_not_exist")
    finally:
        sys.modules.pop("_test_api_callback_attr", None)


# ---- build_example_config -----------------------------------------------


def test_build_example_config_returns_api_configuration():
    cfg = build_example_config()
    assert isinstance(cfg, ApiConfiguration)
    assert cfg.title == "Algomancy API (Example)"
    assert cfg.autorun is False  # explicit choice — see main.py


# ---- main() exit paths --------------------------------------------------


def test_main_without_flags_exits_with_code_2(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code == 2
    err = capsys.readouterr().out + capsys.readouterr().err
    assert "config-callback" in err or "example" in err


def test_main_dispatches_to_callback(monkeypatch, api_core_kwargs):
    """main() should call ApiLauncher.build with the callback's return value
    and then ApiLauncher.run; we patch run() so the test doesn't start uvicorn."""

    def make_config() -> ApiConfiguration:
        return ApiConfiguration(**api_core_kwargs)

    _install_fake_module("_test_api_main_dispatch", {"make_config": make_config})
    try:
        import algomancy_api.api_launcher as launcher_mod

        run_calls: list[tuple] = []

        def fake_run(app, host=None, port=None):
            run_calls.append((app, host, port))

        monkeypatch.setattr(launcher_mod.ApiLauncher, "run", staticmethod(fake_run))

        main(
            [
                "--config-callback",
                "_test_api_main_dispatch:make_config",
                "--port",
                "9999",
            ]
        )

        assert len(run_calls) == 1
        app, host, port = run_calls[0]
        assert host is None
        assert port == 9999
    finally:
        sys.modules.pop("_test_api_main_dispatch", None)
