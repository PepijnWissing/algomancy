"""Verify the quickstart templates produce code aligned with the post-M7
``algomancy_data`` API.

These tests render each modernized template with a representative context
and assert that the output:

* parses as valid Python (``ast.parse``)
* uses the new ``Column`` / ``ColumnGroup`` symbols
* avoids the deprecated ``_DATATYPES`` / ``_defined_datatypes`` patterns
* declares ETL factories that delegate to ``super()`` for the M4 defaults
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest
from jinja2 import Environment, PackageLoader, select_autoescape

from algomancy_data import DataType, FileExtension


@pytest.fixture
def jinja_env() -> Environment:
    return Environment(
        loader=PackageLoader("algomancy_quickstart", "templates"),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _csv_file_info() -> SimpleNamespace:
    return SimpleNamespace(
        file_path=Path("data/setup/orders.csv"),
        file_name="orders",
        class_name="Orders",
        snake_name="orders",
        extension=FileExtension.CSV,
        sheet_names=[],
        selected_sheets=[],
        csv_separator=",",
        skip_file=False,
        is_multi_sheet=False,
        sheets_to_extract=[],
        total_columns=3,
        inferred_schemas={
            "default": {
                "order_id": DataType.STRING,
                "amount": DataType.FLOAT,
                "created_at": DataType.DATETIME,
            }
        },
        primary_key_columns={"default": ["order_id"]},
    )


def _xlsx_multi_file_info() -> SimpleNamespace:
    return SimpleNamespace(
        file_path=Path("data/setup/regions.xlsx"),
        file_name="regions",
        class_name="Regions",
        snake_name="regions",
        extension=FileExtension.XLSX,
        sheet_names=["EU", "NA"],
        selected_sheets=["EU", "NA"],
        csv_separator=",",
        skip_file=False,
        is_multi_sheet=True,
        sheets_to_extract=["EU", "NA"],
        total_columns=4,
        inferred_schemas={
            "EU": {"country": DataType.STRING, "population": DataType.INTEGER},
            "NA": {"country": DataType.STRING, "population": DataType.INTEGER},
        },
        primary_key_columns={"EU": ["country"], "NA": ["country"]},
    )


def _xlsx_single_file_info() -> SimpleNamespace:
    return SimpleNamespace(
        file_path=Path("data/setup/inventory.xlsx"),
        file_name="inventory",
        class_name="Inventory",
        snake_name="inventory",
        extension=FileExtension.XLSX,
        sheet_names=["Sheet1"],
        selected_sheets=["Sheet1"],
        csv_separator=",",
        skip_file=False,
        is_multi_sheet=False,
        sheets_to_extract=["Sheet1"],
        total_columns=2,
        inferred_schemas={
            "default": {"sku": DataType.STRING, "qty": DataType.INTEGER},
        },
        primary_key_columns={"default": ["sku"]},
    )


def _assert_parses(rendered: str) -> ast.Module:
    try:
        return ast.parse(rendered)
    except SyntaxError as exc:  # pragma: no cover - surfaced via assert
        raise AssertionError(
            f"Rendered template is not valid Python: {exc}\n\n{rendered}"
        ) from exc


def test_schema_template_emits_column_attributes(jinja_env: Environment) -> None:
    tmpl = jinja_env.get_template("schema.py.jinja")
    rendered = tmpl.render(
        project_name="Orders",
        class_name="Orders",
        filename="orders",
    )
    _assert_parses(rendered)

    assert "from algomancy_data import" in rendered
    assert "Column(" in rendered
    assert "all_schemas" in rendered
    assert "_defined_datatypes" not in rendered
    assert "_DATATYPES" not in rendered


def test_generated_schemas_single_emits_columns(jinja_env: Environment) -> None:
    tmpl = jinja_env.get_template("generated_schemas.py.jinja")
    rendered = tmpl.render(
        project_name="Demo",
        files=[_csv_file_info()],
    )
    _assert_parses(rendered)

    assert "Column(" in rendered
    assert "ColumnGroup" not in rendered.split("class OrdersSchema")[1]
    assert "primary_key=True" in rendered  # PK heuristic surfaced
    assert "_defined_datatypes" not in rendered
    assert "all_schemas" in rendered


def test_generated_schemas_multi_emits_columngroup(jinja_env: Environment) -> None:
    tmpl = jinja_env.get_template("generated_schemas.py.jinja")
    rendered = tmpl.render(
        project_name="Demo",
        files=[_xlsx_multi_file_info()],
    )
    _assert_parses(rendered)

    assert "ColumnGroup(" in rendered
    assert "SchemaType.MULTI" in rendered
    assert "_defined_datatypes" not in rendered


def test_etl_factory_template_uses_super(jinja_env: Environment) -> None:
    tmpl = jinja_env.get_template("etl_factory.py.jinja")
    rendered = tmpl.render(project_name="Demo", class_name="Demo")
    _assert_parses(rendered)

    assert "super().create_extraction_sequence" in rendered
    assert "super().create_validation_sequence" in rendered
    # Should not redeclare an explicit __init__ — base class handles it
    assert "def __init__" not in rendered
    # Should not override the loader (default is fine)
    assert "def create_loader" not in rendered


def test_etl_factory_generated_with_all_default_files(jinja_env: Environment) -> None:
    tmpl = jinja_env.get_template("etl_factory_generated.py.jinja")
    rendered = tmpl.render(
        project_name="Demo",
        class_name="Demo",
        files=[_csv_file_info()],
        file_count=1,
        default_files=[_csv_file_info()],
        custom_files=[],
        needs_csv_extractor=False,
        needs_xlsx_single_extractor=False,
    )
    _assert_parses(rendered)

    assert "super().create_extraction_sequence" in rendered
    assert "super().create_validation_sequence" in rendered
    assert "ExtractionSuccessVerification" not in rendered
    assert "def __init__" not in rendered


def test_etl_factory_generated_with_custom_xlsx_single(
    jinja_env: Environment,
) -> None:
    tmpl = jinja_env.get_template("etl_factory_generated.py.jinja")
    rendered = tmpl.render(
        project_name="Demo",
        class_name="Demo",
        files=[_xlsx_single_file_info()],
        file_count=1,
        default_files=[],
        custom_files=[_xlsx_single_file_info()],
        needs_csv_extractor=False,
        needs_xlsx_single_extractor=True,
    )
    _assert_parses(rendered)

    assert "XLSXSingleExtractor" in rendered
    assert 'sheet_name="Sheet1"' in rendered
    assert 'self.get_schema("inventory")' in rendered


def test_main_custom_uses_all_schemas(jinja_env: Environment) -> None:
    tmpl = jinja_env.get_template("main.py.jinja")
    rendered = tmpl.render(
        title="Demo",
        host="127.0.0.1",
        port=8050,
        interfaces=["gui"],
        class_name="Demo",
        filename="demo",
        has_custom_implementations=True,
        has_generated_etl=False,
        has_styling=False,
    )
    _assert_parses(rendered)

    assert "from src.data_handling.schemas import all_schemas" in rendered
    assert "schemas=all_schemas" in rendered
    assert "demo_schema" not in rendered


def test_data_file_info_seeds_class_name_from_filename() -> None:
    """``DataFileInfo`` defaults ``class_name`` from the file stem so the
    schema template never renders an empty (and thus colliding) class name
    when downstream metadata enrichment is skipped."""
    from algomancy_quickstart.data_inference import DataFileInfo

    info = DataFileInfo(
        file_path=Path("data/setup/case.json"),
        file_name="case",
        extension=FileExtension.JSON,
    )

    assert info.class_name == "Case"
    assert info.snake_name == "case"


def test_generated_schemas_emits_unique_class_names_for_multiple_files(
    jinja_env: Environment,
) -> None:
    """Regression for #129 — two files in the same project must render two
    distinctly named schema classes, not two ``class Schema(Schema)`` lines
    that shadow the imported ``Schema`` symbol."""
    from algomancy_quickstart.data_inference import DataFileInfo

    case_info = DataFileInfo(
        file_path=Path("data/setup/case.json"),
        file_name="case",
        extension=FileExtension.JSON,
    )
    case_info.inferred_schemas["default"] = {"CallbackURL": DataType.STRING}
    case_info.primary_key_columns["default"] = []
    case_info.total_columns = 1

    results_info = DataFileInfo(
        file_path=Path("data/setup/results.json"),
        file_name="results",
        extension=FileExtension.JSON,
    )
    results_info.inferred_schemas["default"] = {"PickOrders": DataType.STRING}
    results_info.primary_key_columns["default"] = []
    results_info.total_columns = 1

    tmpl = jinja_env.get_template("generated_schemas.py.jinja")
    rendered = tmpl.render(project_name="SWS", files=[case_info, results_info])
    _assert_parses(rendered)

    assert "class CaseSchema(Schema)" in rendered
    assert "class ResultsSchema(Schema)" in rendered
    # No bare ``class Schema(Schema)`` line (that would shadow the import).
    assert "class Schema(Schema)" not in rendered


def _gui_ctx(**overrides: object) -> dict:
    base = dict(
        title="Demo",
        host="127.0.0.1",
        port=8050,
        interfaces=["gui"],
        class_name="Demo",
        filename="demo",
        has_custom_implementations=False,
        has_generated_etl=False,
        has_styling=False,
        persistence_backend="json",
        database_url=None,
    )
    base.update(overrides)
    return base


def test_main_template_database_backend_passes_url(jinja_env: Environment) -> None:
    """Regression for #132 — when ``persistence_backend='database'`` is
    selected, the generated main.py must pass the URL into CoreConfig."""
    tmpl = jinja_env.get_template("main.py.jinja")
    rendered = tmpl.render(
        **_gui_ctx(
            persistence_backend="database",
            database_url="sqlite:///myapp.db",
        )
    )
    _assert_parses(rendered)

    assert 'persistence_backend="database"' in rendered
    assert 'database_url="sqlite:///myapp.db"' in rendered
    assert "has_persistent_state=True" in rendered


def test_main_template_json_backend_omits_database_url(
    jinja_env: Environment,
) -> None:
    tmpl = jinja_env.get_template("main.py.jinja")
    rendered = tmpl.render(**_gui_ctx(persistence_backend="json"))
    _assert_parses(rendered)

    assert 'persistence_backend="json"' in rendered
    assert "database_url=" not in rendered


@pytest.mark.parametrize(
    "template_name",
    [
        "test_algorithm.py.jinja",
        "test_kpi.py.jinja",
    ],
)
def test_pytest_skeletons_parse(jinja_env: Environment, template_name: str) -> None:
    """Regression for #59 — every generated pytest skeleton must parse as
    valid Python so users can run ``pytest`` straight after the wizard."""
    tmpl = jinja_env.get_template(template_name)
    rendered = tmpl.render(project_name="Demo", class_name="Demo", filename="demo")
    _assert_parses(rendered)
    assert "import pytest" in rendered
    assert "def test_" in rendered


@pytest.mark.parametrize("has_generated_etl", [True, False])
def test_pytest_etl_skeleton_parses(
    jinja_env: Environment, has_generated_etl: bool
) -> None:
    tmpl = jinja_env.get_template("test_etl_factory.py.jinja")
    rendered = tmpl.render(
        project_name="Demo",
        class_name="Demo",
        filename="demo",
        has_generated_etl=has_generated_etl,
        has_custom_implementations=not has_generated_etl,
    )
    _assert_parses(rendered)
    if has_generated_etl:
        assert "generated_schemas" in rendered
    else:
        assert "from src.data_handling.schemas import all_schemas" in rendered


def test_pytest_conftest_parses(jinja_env: Environment) -> None:
    tmpl = jinja_env.get_template("conftest.py.jinja")
    rendered = tmpl.render(project_name="Demo")
    _assert_parses(rendered)
    assert "sys.path.insert" in rendered


def test_main_template_no_persistence(jinja_env: Environment) -> None:
    tmpl = jinja_env.get_template("main.py.jinja")
    rendered = tmpl.render(**_gui_ctx(persistence_backend="none"))
    _assert_parses(rendered)

    assert 'persistence_backend="none"' in rendered
    assert "has_persistent_state=False" in rendered
    assert "database_url=" not in rendered


@pytest.mark.parametrize(
    "ctx",
    [
        _gui_ctx(),
        _gui_ctx(has_custom_implementations=True),
        _gui_ctx(has_generated_etl=True),
        _gui_ctx(has_generated_etl=True, has_custom_implementations=True),
        _gui_ctx(has_styling=True),
        _gui_ctx(
            has_styling=True,
            has_custom_implementations=True,
            has_generated_etl=True,
        ),
    ],
)
def test_main_template_pass_all_subconfigs(jinja_env: Environment, ctx: dict) -> None:
    """The unified main template must instantiate ComparePageConfig +
    FeatureConfig (and PageConfig + StylingConfig) for GUI builds so
    AppConfig never falls back to the deprecated keyword path."""
    tmpl = jinja_env.get_template("main.py.jinja")
    rendered = tmpl.render(**ctx)
    _assert_parses(rendered)

    assert "ComparePageConfig(" in rendered, ctx
    assert "FeatureConfig(" in rendered, ctx
    assert "PageConfig(" in rendered, ctx
    # styling_config either explicit (StylingConfig() or app_styling)
    assert "styling_config=" in rendered, ctx


@pytest.mark.parametrize(
    "interfaces",
    [
        ["gui"],
        ["api"],
        ["gui", "api"],
    ],
)
def test_main_template_supports_interface_combinations(
    jinja_env: Environment, interfaces: list
) -> None:
    """Regression for #128 — the generated main.py must include only the
    launchers for the interfaces the user chose."""
    tmpl = jinja_env.get_template("main.py.jinja")
    rendered = tmpl.render(**_gui_ctx(interfaces=interfaces))
    _assert_parses(rendered)

    if "gui" in interfaces:
        assert "GuiLauncher" in rendered
        assert "run_gui" in rendered
    else:
        assert "GuiLauncher" not in rendered

    if "api" in interfaces:
        assert "ApiLauncher" in rendered
        assert "run_api" in rendered
    else:
        assert "ApiLauncher" not in rendered

    if len(interfaces) > 1:
        # Multi-interface mains must dispatch on --interface.
        assert "--interface" in rendered
    else:
        # Single-interface mains skip argparse and just call the launcher.
        assert "--interface" not in rendered
