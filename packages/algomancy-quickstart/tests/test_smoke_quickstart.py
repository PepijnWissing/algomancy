"""Quickstart end-to-end smoke test.

For each combination of (backend × interface), this test:

1. Creates a ``tmp_path`` working directory.
2. Runs ``wizard.step_1_create_structure()`` with mocked click prompts to
   generate ``main.py`` without user interaction.
3. Verifies that ``main.py`` is present and parses as valid Python.
4. Runs ``python main.py --validate`` and asserts exit 0.

The ``database`` backend variant uses a SQLite URL so no external service
is required.

Marked ``@pytest.mark.slow`` for the subprocess-based validate tests.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from algomancy_quickstart.quickstart import QuickstartWizard

REPO_ROOT = Path(__file__).resolve().parents[4]

_INTERFACE_BACKEND_MATRIX = [
    ("gui", "json"),
    ("cli", "json"),
    ("api", "json"),
    ("gui", "none"),
    ("gui", "database"),
    # Multi-interface combo
    ("gui,cli,api", "json"),
]


def _make_wizard(tmp_path: Path, interface: str, backend: str) -> QuickstartWizard:
    """Construct a QuickstartWizard with all click prompts mocked out."""
    wizard = QuickstartWizard(skip_confirmation=True, title="Smoke Test App")
    wizard.current_dir = tmp_path

    interfaces = [i.strip() for i in interface.split(",")]
    database_url = "sqlite:///./smoke_test.db" if backend == "database" else None

    # Pre-set wizard attributes so step_1 prompts can be bypassed
    wizard.title = "Smoke Test App"
    wizard.host = "127.0.0.1"
    wizard.port = 8050
    wizard.interfaces = interfaces
    wizard.persistence_backend = backend
    wizard.database_url = database_url

    return wizard


@pytest.mark.parametrize("interface,backend", _INTERFACE_BACKEND_MATRIX)
def test_generated_main_py_parses(tmp_path, interface, backend):
    """main.py produced by step_1 must be valid Python."""
    wizard = _make_wizard(tmp_path, interface, backend)

    # wizard.title is pre-set so that prompt is skipped.
    # Remaining prompts in order: host, port, interfaces, backend, [database_url].
    database_url = "sqlite:///./smoke_test.db"
    prompts = [
        "127.0.0.1",  # host
        8050,  # port (int — mock returns it as-is)
        interface,  # interfaces
        backend,  # persistence backend
        database_url,  # database_url (only consumed for 'database' backend)
    ]

    with (
        patch("click.prompt", side_effect=prompts),
        patch("click.confirm", return_value=True),
        patch("click.echo"),
    ):
        wizard.step_1_create_structure()

    main_py = tmp_path / "main.py"
    assert main_py.exists(), "main.py was not created"

    source = main_py.read_text()
    try:
        ast.parse(source)
    except SyntaxError as exc:
        pytest.fail(f"main.py has syntax errors: {exc}\n\nSource:\n{source}")


@pytest.mark.slow
@pytest.mark.parametrize("interface,backend", _INTERFACE_BACKEND_MATRIX)
def test_generated_main_py_validate_exits_zero(tmp_path, interface, backend):
    """python main.py --validate must exit 0 for every interface/backend combo."""
    wizard = _make_wizard(tmp_path, interface, backend)

    prompts = [
        "127.0.0.1",
        8050,
        interface,
        backend,
        "sqlite:///./smoke_test.db",
    ]

    with (
        patch("click.prompt", side_effect=prompts),
        patch("click.confirm", return_value=True),
        patch("click.echo"),
    ):
        wizard.step_1_create_structure()

    main_py = tmp_path / "main.py"
    assert main_py.exists(), "main.py was not created"

    interfaces = [i.strip() for i in interface.split(",")]
    # Test each interface in the combo
    for iface in interfaces:
        result = subprocess.run(
            [
                sys.executable,
                str(main_py),
                "--interface",
                iface,
                "--validate",
            ]
            if len(interfaces) > 1
            else [sys.executable, str(main_py), "--validate"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=30,
        )
        assert result.returncode == 0, (
            f"--validate failed for interface={iface}, backend={backend}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert "[validate]" in result.stdout and "OK" in result.stdout, (
            f"Expected '[validate] ... OK' in stdout.\n{result.stdout}"
        )
