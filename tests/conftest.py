"""Shared pytest helpers for live-subprocess smoke tests.

These utilities are used by the API, CLI, GUI, and quickstart smoke tests so
they share the same subprocess lifecycle, port selection, and health-poll logic.

Helpers:
- ``find_free_port()`` — grab an OS-assigned ephemeral port (release before use).
- ``wait_for_http(url, ...)`` — poll a URL until it responds 200 or timeout.
- ``live_subprocess(cmd, ...)`` — context manager that starts, waits, and tears
  down a subprocess; streams stdout/stderr to a log file for debuggability.
- ``REPO_ROOT`` — absolute path to the repository root.
"""

from __future__ import annotations

import os
import pathlib
import socket
import subprocess
import time
from contextlib import contextmanager

import pytest

REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parent.parent


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
    """Poll *url* with GET until HTTP 200, or fail with diagnostics.

    If *proc* is supplied and exits before the deadline the helper immediately
    surfaces the log file contents so the failure is actionable.

    Args:
        url: Full URL to poll (e.g. ``http://127.0.0.1:8051/health``).
        timeout_seconds: Maximum seconds to wait before declaring failure.
        proc: Optional subprocess whose exit signals premature failure.
        log_path: Path to the subprocess log file; surfaced on failure.
    """
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

    Stdout and stderr are redirected to *log_path* so pipes can't fill and
    block the process. The file is left on disk for inspection on failure.

    Args:
        cmd: Command + arguments list.
        log_path: File path for combined stdout/stderr output.
        cwd: Working directory for the subprocess (default: repo root).
        extra_env: Extra environment variables to overlay on os.environ.
        shutdown_timeout: Seconds to wait for clean exit before SIGKILL.

    Yields:
        The running :class:`subprocess.Popen` object.
    """
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)

    log_file = open(log_path, "w", encoding="utf-8")
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
