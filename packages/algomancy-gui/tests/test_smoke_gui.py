"""GUI smoke test using Playwright.

Spawns ``python -m example.main --interface gui --port <free>`` and uses
Playwright to verify the dashboard renders something meaningful:

1. Landing page returns 200 and contains the dashboard title.
2. Scenarios page renders at least one registered algorithm (asserts a
   *concrete* algorithm name, not the generic ``<select>`` element).

Marked ``@pytest.mark.gui`` and ``@pytest.mark.slow`` so it only runs in the
full GUI CI lane (not the fast PR path).  Skipped automatically when
``playwright`` is not installed (``playwright install chromium`` required).

Failure screenshots are saved to ``pytest-results/`` for artifact upload.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

from algomancy_utils._smoke_helpers import (
    REPO_ROOT,
    find_free_port,
    live_subprocess,
    wait_for_http,
)

pytestmark = [pytest.mark.gui, pytest.mark.slow]

_RESULTS_DIR = REPO_ROOT / "pytest-results"


@pytest.fixture(scope="module", autouse=True)
def _require_playwright():
    # Module-level importorskip would fire during collection, before marker
    # filtering, creating a spurious skip on the fast PR path. Using a fixture
    # defers the check until pytest actually selects tests from this module.
    pytest.importorskip(
        "playwright",
        reason="playwright not installed — run 'playwright install chromium'",
    )


# Concrete algorithm names registered on `better-example` (and ancestors of
# this branch). The dropdown must include AT LEAST ONE — asserting on a list
# instead of a single name keeps the test robust to registry tweaks while
# still failing if the algorithm registry is silently empty.
_REGISTERED_ALGOS_LOWER = [
    "instant",
    "greedy slotting",
    "asis slotting",
    "sa slotting",
]


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
def test_landing_page_renders_dashboard_title(gui_base_url):
    """The landing page must render the configured app title."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(gui_base_url, wait_until="domcontentloaded")
            page.screenshot(path=str(_screenshot_dir() / "gui_landing.png"))
            content = page.content().lower()
            # The example's StylingConfig sets title="Example implementation of
            # an Algomancy Dashboard"; assert on a distinctive substring rather
            # than a generic token that any HTML page would contain.
            assert "algomancy dashboard" in content, (
                f"Expected configured app title in landing page.\nURL: {page.url}"
            )
        except Exception:
            page.screenshot(path=str(_screenshot_dir() / "gui_landing_fail.png"))
            raise
        finally:
            browser.close()


@pytest.mark.gui
@pytest.mark.slow
def test_scenarios_page_renders_registered_algorithm(gui_base_url):
    """The scenarios page must render at least one registered algorithm name.

    The algorithm dropdown lives inside the 'Create New Scenario' modal, so we
    open the modal before checking.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(f"{gui_base_url}/scenarios", wait_until="domcontentloaded")
            # Wait for Dash to finish hydrating the page.
            page.wait_for_timeout(1500)

            # Open the Create New Scenario modal so the algorithm dropdown
            # is rendered into the DOM.
            page.click("#scenario-creator-open-btn")
            page.wait_for_selector("#scenario-algo-input", timeout=5000)

            # Click the dropdown to open the option list; React Select only
            # renders option text into the DOM when the menu is open.
            page.click("#scenario-algo-input .Select-control, #scenario-algo-input")
            page.wait_for_timeout(800)

            page.screenshot(path=str(_screenshot_dir() / "gui_scenarios.png"))
            content = page.content().lower()

            matches = [a for a in _REGISTERED_ALGOS_LOWER if a in content]
            assert matches, (
                f"Expected at least one registered algorithm name in the "
                f"scenarios page after opening the algorithm dropdown; "
                f"tried {_REGISTERED_ALGOS_LOWER}.\n"
                f"URL: {page.url}"
            )
        except Exception:
            page.screenshot(path=str(_screenshot_dir() / "gui_scenarios_fail.png"))
            raise
        finally:
            browser.close()
