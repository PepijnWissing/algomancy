"""CLI smoke test — drives the REPL via stdin/stdout pipe.

Spawns ``python -m algomancy_cli.main --example`` and pipes a scripted command
sequence into stdin. The test asserts that expected tokens appear in stdout and
that the process exits cleanly.

Wall-clock budget: 30 s (covers ETL startup + a 1-second Slow scenario run).

Marked ``@pytest.mark.slow`` so it can be excluded from the fast PR path.
"""

from __future__ import annotations

import subprocess
import sys
import time

import pytest

from tests.conftest import REPO_ROOT

pytestmark = pytest.mark.slow

_STARTUP_TIMEOUT = 30.0
_COMMANDS = "\n".join(
    [
        "list-data",
        "list-scenarios",
        'create-scenario smoke-cli default_session Slow {"duration": 1}',
        "run smoke-cli",
        "list-scenarios",
        "exit",
    ]
)


@pytest.mark.slow
def test_cli_repl_smoke():
    """Drive the CLI shell through a representative session.

    Sequence: list-data → list-scenarios → create + run a Slow scenario →
    list-scenarios again → exit.
    """
    cmd = [
        sys.executable,
        "-m",
        "algomancy_cli.main",
        "--example",
    ]
    start = time.monotonic()
    result = subprocess.run(
        cmd,
        input=_COMMANDS,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=_STARTUP_TIMEOUT,
    )
    elapsed = time.monotonic() - start

    combined = result.stdout + result.stderr

    # Session list should include the example sessions
    assert "default_session" in combined or "example_data" in combined, (
        f"Expected session/data names in output. Combined:\n{combined}"
    )

    # Slow algorithm should be discoverable (via list-scenarios or scenario name)
    assert "smoke-cli" in combined or "Slow" in combined, (
        f"Expected scenario or algorithm token in output. Combined:\n{combined}"
    )

    assert elapsed < _STARTUP_TIMEOUT, (
        f"CLI took {elapsed:.1f}s (limit: {_STARTUP_TIMEOUT}s)"
    )

    # Process should exit cleanly (0 or the standard 'exit' sentinel)
    # The CLI exits via EOFError on stdin close which is exit code 0
    assert result.returncode == 0, (
        f"CLI exited with code {result.returncode}.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
