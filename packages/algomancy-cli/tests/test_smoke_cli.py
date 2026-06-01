"""CLI smoke test — drives the REPL via stdin/stdout pipe.

Spawns ``python -m algomancy_cli.main --example`` and pipes a scripted command
sequence into stdin. The test asserts that expected tokens appear in stdout and
that the process exits cleanly.

Wall-clock budget: 30 s (covers ETL startup + an Instant scenario run).

Marked ``@pytest.mark.slow`` so it can be excluded from the fast PR path.
"""

from __future__ import annotations

import subprocess
import sys
import time

import pytest

from algomancy_utils._smoke_helpers import REPO_ROOT

pytestmark = pytest.mark.slow

_STARTUP_TIMEOUT = 30.0
_COMMANDS = "\n".join(
    [
        "list-data",
        "list-scenarios",
        "create-scenario smoke-cli example_data Instant {}",
        "run smoke-cli",
        "list-scenarios",
        "exit",
    ]
)


@pytest.mark.slow
def test_cli_repl_smoke():
    """Drive the CLI shell through a representative session.

    Sequence: list-data → list-scenarios → create + run an Instant scenario →
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

    # CLI must boot cleanly.
    assert result.returncode == 0, (
        f"CLI exited with code {result.returncode}.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert elapsed < _STARTUP_TIMEOUT, (
        f"CLI took {elapsed:.1f}s (limit: {_STARTUP_TIMEOUT}s)"
    )

    # The example dataset must be discoverable via `list-data`.
    assert "example_data" in combined, (
        f"Expected dataset 'example_data' in output.\nCombined:\n{combined}"
    )

    # `create-scenario smoke-cli ... Instant {}` succeeds — the shell logs
    # "Created scenario id=<...> tag=smoke-cli" on success. Asserting on the
    # full marker means a bare echo of the input line won't satisfy the test.
    assert "Created scenario" in combined and "smoke-cli" in combined, (
        f"Expected 'Created scenario ... smoke-cli' in output.\nCombined:\n{combined}"
    )

    # `run smoke-cli` should complete; the shell logs "Scenario 'smoke-cli' completed."
    assert "smoke-cli" in combined and "completed" in combined, (
        f"Expected scenario completion log for 'smoke-cli'.\nCombined:\n{combined}"
    )
