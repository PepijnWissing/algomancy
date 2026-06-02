"""Override-safety tests for the wizard.

Covers the three classes of bug surfaced in the file-write audit:

* **B1** — ``has_generated_etl`` ordering. After step 3 runs in an API-only
  project, ``main.py`` must import ``all_schemas`` from
  ``generated_schemas.py`` (the file step 3 just wrote), NOT from
  ``schemas.py`` (the step-2 stub). Previously the flag was set in
  ``run()`` after step 3 returned, so step 3's own main.py render saw
  ``has_generated_etl=False`` and emitted the wrong import.
* **B2** — declining the final "Generate ETL with these configurations?"
  prompt must leave ``has_generated_etl=False`` (no files were written).
* **B5** — re-running the wizard against an existing project must NOT
  silently clobber user-edited ``generated_schemas.py``,
  ``styling_config.py``, or ``main.py``.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

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


def _seed_csv(tmp_path: Path) -> None:
    (tmp_path / "data" / "setup").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "setup" / "orders.csv").write_text(
        "id,name\n1,a\n2,b\n", encoding="utf-8"
    )


class TestB1HasGeneratedEtlOrdering:
    """API-only + step 2 + step 3 must end with the right schema import."""

    def test_api_only_main_py_imports_generated_schemas(self, tmp_path):
        _seed_csv(tmp_path)
        wizard = QuickstartWizard(skip_confirmation=True, title="B1 Test")
        wizard.current_dir = tmp_path

        # step 1: host, port, interfaces=api, backend=none
        # step 2: project name
        # step 3 inference: CSV separator (one CSV)
        prompts = ["127.0.0.1", 8050, "api", "none", "B1", ","]
        # step 2 yes, step 3 yes, step 3-per-file yes, step 6 yes
        confirms = [True, True, True, True]

        with (
            patch("click.prompt", side_effect=prompts),
            patch("click.confirm", side_effect=confirms),
            patch("click.echo"),
        ):
            wizard.run()

        main = (tmp_path / "main.py").read_text(encoding="utf-8")
        assert "from src.data_handling.generated_schemas import all_schemas" in main, (
            f"Expected generated_schemas import.\nGot:\n{main}"
        )
        assert "from src.data_handling.schemas import all_schemas" not in main, (
            "Step-2 stub schemas import leaked through despite step 3 running."
        )
        assert wizard.has_generated_etl is True


class TestB2DeclinedFinalConfirmDoesNotFlipFlag:
    """Declining D18 must leave has_generated_etl=False and no ETL files."""

    def test_decline_step3_final_confirm(self, tmp_path):
        _seed_csv(tmp_path)
        # ``not skip_confirmation`` is required for D18 to even surface.
        wizard = QuickstartWizard(skip_confirmation=False, title="B2 Test")
        wizard.current_dir = tmp_path

        prompts = ["127.0.0.1", 8050, "api", "none", "B2", ","]
        # confirms in order:
        #   step 2 yes
        #   step 3 outer yes
        #   step 3 per-file include yes
        #   step 3 final D18 NO       <-- the decline under test
        #   step 6 yes
        # (No per-file overwrite confirms triggered: fresh project, files
        # don't pre-exist. Step 2's main.py write is also fresh.)
        confirms = [True, True, True, False, True]

        with (
            patch("click.prompt", side_effect=prompts),
            patch("click.confirm", side_effect=confirms),
            patch("click.echo"),
        ):
            wizard.run()

        assert wizard.has_generated_etl is False
        assert not (
            tmp_path / "src" / "data_handling" / "generated_schemas.py"
        ).exists()
        main = (tmp_path / "main.py").read_text(encoding="utf-8")
        # Step 2 ran (yes to D9), so main.py uses the custom-impl branch
        # pointing at the step-2 stubs — NOT generated_schemas.
        assert "from src.data_handling.schemas import all_schemas" in main
        assert "from src.data_handling.generated_schemas" not in main


class TestB5RerunOverwriteGuards:
    """Files that previously got silently clobbered now ask first."""

    def _seed_full_project(self, tmp_path: Path) -> QuickstartWizard:
        """First wizard pass — produces a GUI project with all artifacts."""
        _seed_csv(tmp_path)
        wizard = QuickstartWizard(skip_confirmation=True, title="Seed")
        wizard.current_dir = tmp_path

        prompts = ["127.0.0.1", 8050, "gui", "none", "Seed", ","]
        # step 2, step 3 outer, step 3 per-file, step 4 assets, step 5
        # styling, step 6 tests
        confirms = [True, True, True, True, True, True]

        with (
            patch("click.prompt", side_effect=prompts),
            patch("click.confirm", side_effect=confirms),
            patch("click.echo"),
            patch.object(wizard.asset_manager, "install_assets", return_value=True),
            patch.object(
                wizard.styling_wizard, "run", return_value=dict(_STYLING_CONFIG_STUB)
            ),
        ):
            wizard.run()
        return wizard

    def test_decline_main_py_overwrite_blocks_subsequent_renders(self, tmp_path):
        """Step 1 D8=no must prevent step 2/3/5 from rewriting main.py."""
        self._seed_full_project(tmp_path)
        sentinel = "# HAND EDITED — DO NOT OVERWRITE\n"
        (tmp_path / "main.py").write_text(sentinel, encoding="utf-8")

        wizard = QuickstartWizard(skip_confirmation=False, title="B5 main.py")
        wizard.current_dir = tmp_path

        # Re-run prompts: host, port, interfaces, backend, project_name, csv_sep
        prompts = ["127.0.0.1", 8050, "gui", "none", "B5", ","]
        # Confirms in order:
        #   1. step 1 folders-exist confirm (yes, continue)
        #   2. step 1 main.py overwrite (NO — the decline under test)
        #   3. step 2 outer yes
        #   4-9. per-file overwrite confirms in step 2 — say NO to keep
        #        the existing files in place (we only care about main.py
        #        here, but declining keeps the test deterministic)
        #   10. step 3 outer yes
        #   11. step 3 per-file include yes
        #   12. step 3 D18 final yes
        #   13. step 3 etl_factory overwrite — NO (keep stub)
        #   14. step 3 generated_schemas overwrite — NO (keep stub)
        #   15. step 4 assets yes
        #   16. step 5 styling yes
        #   17. step 5 styling_config overwrite — NO
        #   18. step 6 tests yes
        #   19-22. test file overwrite confirms — NO
        confirms = [True, False] + [False] * 20

        with (
            patch("click.prompt", side_effect=prompts),
            patch("click.confirm", side_effect=confirms),
            patch("click.echo"),
            patch.object(wizard.asset_manager, "install_assets", return_value=True),
            patch.object(
                wizard.styling_wizard, "run", return_value=dict(_STYLING_CONFIG_STUB)
            ),
        ):
            wizard.run()

        # The sentinel survives — no step rewrote main.py.
        assert (tmp_path / "main.py").read_text(encoding="utf-8") == sentinel

    def test_decline_generated_schemas_overwrite(self, tmp_path):
        """B5: declining the new generated_schemas.py overwrite confirm
        must preserve the user-edited file."""
        self._seed_full_project(tmp_path)
        sentinel = "# user edits go here\nall_schemas = []\n"
        schemas_path = tmp_path / "src" / "data_handling" / "generated_schemas.py"
        schemas_path.write_text(sentinel, encoding="utf-8")

        wizard = QuickstartWizard(skip_confirmation=False, title="B5 schemas")
        wizard.current_dir = tmp_path

        prompts = ["127.0.0.1", 8050, "gui", "none", "B5", ","]
        # 1. folders-exist yes
        # 2. main.py overwrite YES
        # 3. step 2 yes
        # 4-9. step 2 per-file overwrite YES
        # 10. step 3 outer yes
        # 11. step 3 per-file include yes
        # 12. step 3 D18 final yes
        # 13. step 3 etl_factory overwrite YES
        # 14. step 3 generated_schemas overwrite NO  <-- decline under test
        # 15. step 4 assets yes
        # 16. step 5 styling yes
        # 17. step 5 styling_config overwrite YES
        # 18. step 6 tests yes
        # 19-22. test file overwrite YES
        confirms = (
            [True, True, True]
            + [True] * 6
            + [True, True, True, True, False, True, True, True, True]
            + [True] * 4
        )

        with (
            patch("click.prompt", side_effect=prompts),
            patch("click.confirm", side_effect=confirms),
            patch("click.echo"),
            patch.object(wizard.asset_manager, "install_assets", return_value=True),
            patch.object(
                wizard.styling_wizard, "run", return_value=dict(_STYLING_CONFIG_STUB)
            ),
        ):
            wizard.run()

        assert schemas_path.read_text(encoding="utf-8") == sentinel

    def test_decline_styling_config_overwrite(self, tmp_path):
        """B5: declining the new styling_config.py overwrite confirm
        must preserve the user-edited file."""
        self._seed_full_project(tmp_path)
        sentinel = "# user styling\napp_styling = None\n"
        styling_path = tmp_path / "src" / "styling_config.py"
        styling_path.write_text(sentinel, encoding="utf-8")

        wizard = QuickstartWizard(skip_confirmation=False, title="B5 styling")
        wizard.current_dir = tmp_path

        prompts = ["127.0.0.1", 8050, "gui", "none", "B5", ","]
        # Same flow as above; only difference is the styling_config
        # overwrite is declined and earlier ones are accepted.
        confirms = (
            [True, True, True]
            + [True] * 6
            + [True, True, True, True, True, True, True, False, True]
            + [True] * 4
        )

        with (
            patch("click.prompt", side_effect=prompts),
            patch("click.confirm", side_effect=confirms),
            patch("click.echo"),
            patch.object(wizard.asset_manager, "install_assets", return_value=True),
            patch.object(
                wizard.styling_wizard, "run", return_value=dict(_STYLING_CONFIG_STUB)
            ),
        ):
            wizard.run()

        assert styling_path.read_text(encoding="utf-8") == sentinel
