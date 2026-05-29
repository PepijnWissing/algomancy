"""Shared fixtures for algomancy-api tests.

Reuses the example schemas/ETL/algorithm/KPI defined in the algomancy-scenario
test conftest so we don't duplicate framework wiring across packages.
"""

from __future__ import annotations

import pytest

# Import shared example wiring from the scenario package's conftest. This works
# because pytest discovers conftest.py modules but the file is also a regular
# Python module reachable via its path.
import importlib.util
import pathlib

_SCENARIO_CONFTEST = (
    pathlib.Path(__file__).resolve().parents[2]
    / "algomancy-scenario"
    / "tests"
    / "conftest.py"
)


def _load_shared():
    spec = importlib.util.spec_from_file_location(
        "_algomancy_shared_test_fixtures", _SCENARIO_CONFTEST
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_shared = _load_shared()

ExampleETLFactory = _shared.ExampleETLFactory
example_schemas = _shared.example_schemas
algorithm_templates = _shared.algorithm_templates
kpi_templates = _shared.kpi_templates


@pytest.fixture
def api_core_kwargs(tmp_path) -> dict:
    """Minimal kwargs for ApiConfiguration / CoreConfig in tests.

    Uses a tmp_path so each test gets an isolated, writable data folder when
    ``has_persistent_state=True``.
    """
    from algomancy_data import DataSource

    return {
        "data_path": str(tmp_path),
        "has_persistent_state": True,
        "save_type": "json",
        "data_object_type": DataSource,
        "etl_factory": ExampleETLFactory,
        "schemas": example_schemas,
        "kpi_templates": kpi_templates,
        "algo_templates": algorithm_templates,
        "autocreate": False,
        "autorun": False,
    }
