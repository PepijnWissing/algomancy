"""Shared helpers for live-subprocess smoke tests.

Lives in ``algomancy_utils`` (under a private name) so test modules in any of
the workspace packages can import it without having to manipulate ``sys.path``
or rely on pytest's rootdir-relative ``tests/`` directory being importable.

Not part of the public API — use only from tests.

Helpers:
- ``find_free_port()`` — grab an OS-assigned ephemeral port (release before use).
- ``wait_for_http(url, ...)`` — poll a URL until it responds 200 or timeout.
- ``live_subprocess(cmd, ...)`` — context manager that starts, waits, and tears
  down a subprocess; streams stdout/stderr to a log file for debuggability.
- ``REPO_ROOT`` — absolute path to the repository root (resolved at import time
  from this file's location).
"""

from __future__ import annotations

import os
import pathlib
import socket
import subprocess
import time
from contextlib import contextmanager

import pytest

# packages/algomancy-utils/src/algomancy_utils/_smoke_helpers.py → up 4 → repo root
REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[4]


def find_free_port() -> int:
    """Bind to port 0 to obtain an OS-assigned free port, then release it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for_http(
    url: str,
    *,
    timeout_seconds: float = 30.0,
    proc: subprocess.Popen | None = None,
    log_path: pathlib.Path | None = None,
) -> None:
    """Poll *url* with GET until HTTP 200, or fail with diagnostics."""
    import httpx

    deadline = time.monotonic() + timeout_seconds
    last_err: Exception | None = None

    while time.monotonic() < deadline:
        if proc is not None and proc.poll() is not None:
            log_text = (
                log_path.read_text(errors="replace")
                if log_path and log_path.exists()
                else ""
            )
            pytest.fail(
                f"Subprocess exited with code {proc.returncode} before becoming healthy.\n"
                f"Logs:\n{log_text}"
            )
        try:
            r = httpx.get(url, timeout=1.0)
            if r.status_code == 200:
                return
        except httpx.HTTPError as exc:
            last_err = exc
        time.sleep(0.25)

    log_text = (
        log_path.read_text(errors="replace") if log_path and log_path.exists() else ""
    )
    pytest.fail(
        f"URL {url} did not return 200 within {timeout_seconds}s; "
        f"last error: {last_err}\nLogs:\n{log_text}"
    )


@contextmanager
def live_subprocess(
    cmd: list[str],
    *,
    log_path: pathlib.Path,
    cwd: pathlib.Path | str = REPO_ROOT,
    extra_env: dict[str, str] | None = None,
    shutdown_timeout: float = 5.0,
):
    """Context manager that starts a subprocess and tears it down cleanly.

    Stdout and stderr are line-buffered to *log_path* so crash logs reach disk
    even on immediate subprocess exit. The file is left on disk for inspection
    on failure.
    """
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)

    # buffering=1 → line-buffered: ensures partial output is on disk if the
    # subprocess crashes before flushing, so error diagnostics are surfaceable.
    log_file = open(log_path, "w", encoding="utf-8", buffering=1)
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        yield proc
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=shutdown_timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=shutdown_timeout)
        log_file.close()
