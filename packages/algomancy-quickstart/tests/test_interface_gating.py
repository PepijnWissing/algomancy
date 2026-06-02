"""Verify the quickstart wizard only emits files relevant to the selected
interface(s) — issue #170.

These tests drive the wizard end-to-end against the full prompt sequence
(with click prompts mocked) and assert that GUI-only artifacts (``assets/``,
``src/pages/``, ``src/styling_config.py``) are present for GUI projects and
absent for API-only projects.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from algomancy_gui.configuration.colorconfig import ButtonColorMode, CardHighlightMode

from algomancy_quickstart.quickstart import QuickstartWizard


_STYLING_CONFIG_STUB = {
    "background": "#FFFFFF",
    "primary": "#000000",
    "secondary": "#666666",
    "text": "#222222",
    "text_highlight": "#000000",
    "text_selected": "#FFFFFF",
    "button_mode": ButtonColorMode.UNIFIED,
    "card_mode": CardHighlightMode.LIGHT,
    "logo_path": None,
    "button_path": None,
}


def _run_wizard(
    tmp_path: Path,
    *,
    interfaces: str,
    backend: str = "none",
    do_custom: bool = True,
    do_etl: bool = False,
    do_assets: bool = True,
    do_styling: bool = True,
    do_tests: bool = True,
) -> QuickstartWizard:
    """Drive the full wizard with mocked click prompts.

    Returns the populated wizard for the caller to make assertions on.
    """
    wizard = QuickstartWizard(skip_confirmation=True, title="Gate Test App")
    wizard.current_dir = tmp_path

    # ``click.prompt`` is consumed in order across steps:
    #   step 1: host, port, interfaces, backend, (database_url if backend=db)
    #   step 2: project name
    #   step 3: (only if scanning succeeds — skipped here)
    prompts: list = [
        "127.0.0.1",  # host
        8050,  # port
        interfaces,  # interfaces
        backend,  # backend
    ]
    if backend == "database":
        prompts.append("sqlite:///./gate_test.db")
    prompts.append("Gate")  # step 2 project name

    # ``click.confirm`` order matches the wizard's ``run()`` body:
    #   step 2 (custom impls), step 3 (etl), step 4 (assets - GUI only),
    #   step 5 (styling - GUI only), step 6 (tests).
    confirms: list[bool] = [do_custom, do_etl]
    if "gui" in interfaces:
        confirms.extend([do_assets, do_styling])
    confirms.append(do_tests)

    with (
        patch("click.prompt", side_effect=prompts),
        patch("click.confirm", side_effect=confirms),
        patch("click.echo"),
        # Step 4 reaches out to GitHub for default assets — short-circuit it
        # so the test stays offline. We only care that the prompt was made.
        patch.object(wizard.asset_manager, "install_assets", return_value=True),
        # Step 5's interactive styling wizard has its own click prompt
        # ladder; stub it out and return a canned config so the wizard
        # treats the step as successful and renders ``main.py`` with the
        # ``has_styling=True`` branch.
        patch.object(
            wizard.styling_wizard, "run", return_value=dict(_STYLING_CONFIG_STUB)
        ),
    ):
        wizard.run()

    return wizard


class TestApiOnlyNoGuiArtifacts:
    """API-only projects must not produce GUI-only files or folders."""

    def test_no_assets_folder(self, tmp_path):
        _run_wizard(tmp_path, interfaces="api")
        assert not (tmp_path / "assets").exists()

    def test_no_pages_folder(self, tmp_path):
        _run_wizard(tmp_path, interfaces="api")
        assert not (tmp_path / "src" / "pages").exists()

    def test_no_styling_config(self, tmp_path):
        _run_wizard(tmp_path, interfaces="api")
        assert not (tmp_path / "src" / "styling_config.py").exists()

    def test_non_gui_artifacts_still_present(self, tmp_path):
        _run_wizard(tmp_path, interfaces="api")
        # main.py, src/, data/setup/, custom impl files all stay.
        assert (tmp_path / "main.py").exists()
        assert (tmp_path / "data" / "setup").exists()
        assert (tmp_path / "src" / "data_handling" / "schemas.py").exists()
        assert (tmp_path / "src" / "data_handling" / "etl_factory.py").exists()
        assert (tmp_path / "src" / "templates" / "algorithm").exists()
        assert (tmp_path / "src" / "templates" / "kpi").exists()


class TestGuiProjectStillHasGuiArtifacts:
    """Regression guard — GUI projects keep emitting all GUI artifacts."""

    def test_assets_folder_created(self, tmp_path):
        _run_wizard(tmp_path, interfaces="gui")
        assert (tmp_path / "assets").exists()

    def test_pages_folder_and_files_created(self, tmp_path):
        _run_wizard(tmp_path, interfaces="gui")
        pages = tmp_path / "src" / "pages"
        assert pages.exists()
        for name in (
            "home_page.py",
            "data_page.py",
            "scenario_page.py",
            "compare_page.py",
            "overview_page.py",
        ):
            assert (pages / name).exists(), f"missing {name}"

    def test_styling_config_created(self, tmp_path):
        _run_wizard(tmp_path, interfaces="gui")
        assert (tmp_path / "src" / "styling_config.py").exists()


class TestMultiInterfaceGetsEverything:
    """``gui,api`` is the union — every GUI artifact should still appear."""

    def test_multi_interface_emits_gui_artifacts(self, tmp_path):
        _run_wizard(tmp_path, interfaces="gui,api")
        assert (tmp_path / "assets").exists()
        assert (tmp_path / "src" / "pages" / "home_page.py").exists()
        assert (tmp_path / "src" / "styling_config.py").exists()


class TestNoUnreferencedFiles:
    """Every emitted ``src/`` Python file must be reachable from ``main.py``.

    We approximate "reachable" by parsing ``main.py`` for ``from src...
    import`` statements and confirming the corresponding modules exist —
    which is the inverse of the audit complaint in #170, where ``main.py``
    didn't import the GUI pages but they were emitted anyway.
    """

    @pytest.mark.parametrize("interfaces", ["gui", "api", "gui,api"])
    def test_no_orphan_src_modules(self, tmp_path, interfaces):
        _run_wizard(tmp_path, interfaces=interfaces)

        # Collect ``.py`` files under src/ (excluding __init__.py).
        src_files: set[Path] = set()
        src_root = tmp_path / "src"
        for path in src_root.rglob("*.py"):
            if path.name == "__init__.py":
                continue
            src_files.add(path.relative_to(tmp_path))

        # Approximate reachability: read main.py and walk imports recursively.
        main_py = (tmp_path / "main.py").read_text(encoding="utf-8")
        reachable: set[Path] = set()
        frontier = [main_py]
        while frontier:
            source = frontier.pop()
            for line in source.splitlines():
                line = line.strip()
                if not line.startswith("from src."):
                    continue
                # e.g. "from src.pages.home_page import X"
                module = line.split()[1]
                rel = Path(*module.split(".")).with_suffix(".py")
                if rel in reachable:
                    continue
                target = tmp_path / rel
                if target.exists():
                    reachable.add(rel)
                    frontier.append(target.read_text(encoding="utf-8"))

        # For an API-only project, no ``src/pages/`` files should exist at
        # all — the strongest form of "no orphans". The reachability check
        # below subsumes this but the explicit message is more useful.
        if "gui" not in interfaces:
            orphan_pages = {p for p in src_files if p.parts[:2] == ("src", "pages")}
            assert not orphan_pages, f"API-only project shipped pages: {orphan_pages}"

        # Any src file that exists but is not reachable from main.py is an
        # orphan. Files under ``src/data_handling/`` are always reachable
        # because main.py imports them directly; ``src/templates/...`` are
        # imported when ``has_custom_implementations``.
        orphans = src_files - reachable
        assert not orphans, (
            f"Unreferenced src files for interfaces={interfaces}: {sorted(orphans)}"
        )
