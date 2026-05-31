"""Tests for M10 — Multi-interface example entry point."""

import subprocess
import sys


def _run_validate(
    interface: str, extra: list[str] | None = None
) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable,
        "-m",
        "example.main",
        "--interface",
        interface,
        "--validate",
    ] + (extra or [])
    return subprocess.run(cmd, capture_output=True, text=True)


class TestValidateFlag:
    def test_gui_validate_exits_zero(self):
        result = _run_validate("gui")
        assert result.returncode == 0, result.stderr
        assert "[validate] gui wiring OK" in result.stdout

    def test_cli_validate_exits_zero(self):
        result = _run_validate("cli")
        assert result.returncode == 0, result.stderr
        assert "[validate] cli wiring OK" in result.stdout

    def test_api_validate_exits_zero(self):
        result = _run_validate("api")
        assert result.returncode == 0, result.stderr
        assert "[validate] api wiring OK" in result.stdout


class TestArgParser:
    def test_default_interface_is_gui(self):
        from unittest.mock import patch

        import sys

        # Parse with no args — should default to gui
        with patch.object(sys, "argv", ["main"]):
            from example.main import _parse_args

            args = _parse_args()
            assert args.interface == "gui"

    def test_default_backend_is_json(self):
        from unittest.mock import patch

        with patch.object(sys, "argv", ["main"]):
            from example.main import _parse_args

            args = _parse_args()
            assert args.backend == "json"

    def test_validate_flag_parsed(self):
        from unittest.mock import patch

        with patch.object(sys, "argv", ["main", "--validate"]):
            from example.main import _parse_args

            args = _parse_args()
            assert args.validate is True


class TestCoreKwargs:
    def _make_args(self, backend: str = "json", database_url: str | None = None):
        import argparse

        return argparse.Namespace(backend=backend, database_url=database_url)

    def test_json_backend_has_persistent_state(self):
        from example.main import _core_kwargs

        kwargs = _core_kwargs(self._make_args("json"))
        assert kwargs["has_persistent_state"] is True
        assert kwargs.get("persistence_backend") == "json"

    def test_none_backend_no_persistent_state(self):
        from example.main import _core_kwargs

        kwargs = _core_kwargs(self._make_args("none"))
        assert kwargs["has_persistent_state"] is False

    def test_database_backend_url(self):
        from example.main import _core_kwargs

        kwargs = _core_kwargs(self._make_args("database", "sqlite:///./test.db"))
        assert kwargs["has_persistent_state"] is True
        assert kwargs["database_url"] == "sqlite:///./test.db"
