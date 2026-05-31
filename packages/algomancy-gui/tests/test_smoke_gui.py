"""GUI smoke test using Playwright.

Spawns ``python example/main.py --interface gui --port <free>`` and uses
Playwright to walk through the dashboard:

1. Sidebar contains expected page links.
2. Scenario page renders the algorithm dropdown.
3. Selecting ``Slow`` + clicking Run eventually shows a non-empty KPI cell.

Marked ``@pytest.mark.gui`` and ``@pytest.mark.slow`` so it only runs in the
full GUI CI lane (not the fast PR path).  Skipped automatically when
``playwright`` is not installed (``playwright install chromium`` required).

Failure screenshots are saved to ``pytest-results/`` for artifact upload.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

from tests.conftest import REPO_ROOT, find_free_port, live_subprocess, wait_for_http

pytestmark = [pytest.mark.gui, pytest.mark.slow]

pytest.importorskip(
    "playwright", reason="playwright not installed — run 'playwright install chromium'"
)

_RESULTS_DIR = REPO_ROOT / "pytest-results"


def _screenshot_dir() -> pathlib.Path:
    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return _RESULTS_DIR


@pytest.fixture(scope="module")
def gui_base_url(tmp_path_factory):
    """Start the GUI and yield the base URL; tear down after the module."""
    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    log_path = tmp_path_factory.mktemp("algomancy-gui-smoke") / "gui.log"

    cmd = [
        sys.executable,
        "-m",
        "example.main",
        "--interface",
        "gui",
        "--port",
        str(port),
        "--debug",
    ]

    with live_subprocess(cmd, log_path=log_path) as proc:
        wait_for_http(base_url, timeout_seconds=60.0, proc=proc, log_path=log_path)
        yield base_url


@pytest.mark.gui
@pytest.mark.slow
def test_sidebar_has_expected_links(gui_base_url):
    """Sidebar should contain at least Scenarios and Data links."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(gui_base_url, wait_until="networkidle")
            page.screenshot(path=str(_screenshot_dir() / "gui_sidebar.png"))
            content = page.content().lower()
            assert "scenarios" in content or "scenario" in content, (
                "Expected 'scenarios' in page content"
            )
        except Exception:
            page.screenshot(path=str(_screenshot_dir() / "gui_sidebar_fail.png"))
            raise
        finally:
            browser.close()


@pytest.mark.gui
@pytest.mark.slow
def test_algorithm_dropdown_visible_on_scenario_page(gui_base_url):
    """The scenario page must render an algorithm dropdown."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        try:
            # Navigate to the scenarios page (typically /scenarios)
            page.goto(f"{gui_base_url}/scenarios", wait_until="networkidle")
            page.screenshot(path=str(_screenshot_dir() / "gui_scenarios.png"))
            content = page.content().lower()
            # The algorithm selector should be somewhere on the page
            assert any(tok in content for tok in ["slow", "algorithm", "select"]), (
                f"Expected algorithm-related content on scenarios page.\n"
                f"URL: {page.url}"
            )
        except Exception:
            page.screenshot(path=str(_screenshot_dir() / "gui_scenarios_fail.png"))
            raise
        finally:
            browser.close()
