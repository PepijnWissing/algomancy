"""Tests for M9 — Edge-case coverage."""

import pytest

from algomancy_scenario import ScenarioResult
from example.templates.algorithm.edge_failure_modes import FailureModesAlgorithm
from example.templates.algorithm.edge_instant import InstantAlgorithm
from example.templates.algorithm.edge_parameter_matrix import ParameterMatrixAlgorithm
from example.templates.algorithm.edge_progress_long import LongProgressAlgorithm
from example.templates.kpi.edge_kpis import (
    InfKPI,
    NaNKPI,
    NegativeKPI,
    RaisingKPI,
    ZeroAtThresholdKPI,
)
from algomancy_scenario import KpiError


class _FakeData:
    id = "test"
    tables = {}


FAKE = _FakeData()


# ---------------------------------------------------------------------------
# InstantAlgorithm — #143
# ---------------------------------------------------------------------------


class TestInstantAlgorithm:
    def test_returns_scenario_result(self):
        algo = InstantAlgorithm(InstantAlgorithm.initialize_parameters())
        result = algo.run(FAKE)
        assert isinstance(result, ScenarioResult)

    def test_registered_in_templates(self):
        from example.templates.algorithm import algorithm_templates

        assert "Instant" in algorithm_templates


# ---------------------------------------------------------------------------
# LongProgressAlgorithm — #140
# ---------------------------------------------------------------------------


class TestLongProgressAlgorithm:
    def test_registered_in_templates(self):
        from example.templates.algorithm import algorithm_templates

        assert "Long Progress" in algorithm_templates

    def test_cancel_flag_stops_early(self, monkeypatch):
        import example.templates.algorithm.edge_progress_long as _mod

        sleep_calls: list[float] = []
        monkeypatch.setattr(_mod.time, "sleep", lambda s: sleep_calls.append(s))

        params = LongProgressAlgorithm.initialize_parameters()
        params._parameters["seconds"].set_validated_value(10)
        algo = LongProgressAlgorithm(params)
        algo._cancel_event.set()  # pre-cancel

        result = algo.run(FAKE)
        assert isinstance(result, ScenarioResult)
        # No sleep calls because cancel was already set
        assert len(sleep_calls) == 0

    def test_progress_increases(self, monkeypatch):
        import example.templates.algorithm.edge_progress_long as _mod

        monkeypatch.setattr(_mod.time, "sleep", lambda s: None)

        params = LongProgressAlgorithm.initialize_parameters()
        params._parameters["seconds"].set_validated_value(3)
        algo = LongProgressAlgorithm(params)

        progress_values: list[float] = []
        monkeypatch.setattr(algo, "set_progress", lambda v: progress_values.append(v))
        algo.run(FAKE)

        assert len(progress_values) == 3
        for a, b in zip(progress_values, progress_values[1:]):
            assert b > a


# ---------------------------------------------------------------------------
# FailureModesAlgorithm — #141
# ---------------------------------------------------------------------------


class TestFailureModesAlgorithm:
    def test_registered_in_templates(self):
        from example.templates.algorithm import algorithm_templates

        assert "Failure Modes" in algorithm_templates

    def _run_mode(self, mode: str):
        params = FailureModesAlgorithm.initialize_parameters()
        params._parameters["mode"].set_validated_value(mode)
        algo = FailureModesAlgorithm(params)
        return algo.run(FAKE)

    def test_raise_value_error(self):
        with pytest.raises(ValueError):
            self._run_mode("raise_value_error")

    def test_raise_runtime_error(self):
        with pytest.raises(RuntimeError):
            self._run_mode("raise_runtime")

    def test_return_none(self):
        result = self._run_mode("return_none")
        assert result is None

    def test_key_error_in_kpi_returns_result(self):
        result = self._run_mode("key_error_in_kpi")
        assert result is not None

    def test_infinite_loop_capped_returns(self):
        result = self._run_mode("infinite_loop_capped")
        assert isinstance(result, ScenarioResult)


# ---------------------------------------------------------------------------
# ParameterMatrixAlgorithm — #142
# ---------------------------------------------------------------------------


class TestParameterMatrixAlgorithm:
    def test_registered_in_templates(self):
        from example.templates.algorithm import algorithm_templates

        assert "Parameter Matrix" in algorithm_templates

    def test_all_parameter_types_present(self):
        params = ParameterMatrixAlgorithm.initialize_parameters()
        expected = {
            "int_param",
            "float_param",
            "string_param",
            "bool_param",
            "enum_param",
            "multi_enum_param",
            "time_param",
        }
        assert expected.issubset(set(params._parameters.keys()))

    def test_run_returns_result(self):
        algo = ParameterMatrixAlgorithm(
            ParameterMatrixAlgorithm.initialize_parameters()
        )
        result = algo.run(FAKE)
        assert isinstance(result, ScenarioResult)


# ---------------------------------------------------------------------------
# Edge-case KPIs — #144
# ---------------------------------------------------------------------------


class TestEdgeKpis:
    def test_all_registered_in_templates(self):
        from example.templates.kpi import kpi_templates

        # "Raising KPI" is intentionally NOT registered: every registered
        # KPI is attached to every scenario via KpiFactory.create_all(),
        # so a KPI that always raises would mark every scenario "failed"
        # end-to-end. The class is still importable for direct unit tests
        # of the framework's KPI-failure handling.
        for name in [
            "NaN KPI",
            "Inf KPI",
            "Negative KPI",
            "Zero-at-threshold KPI",
        ]:
            assert name in kpi_templates
        assert "Raising KPI" not in kpi_templates

    def test_nan_kpi_value(self):
        import math

        kpi = NaNKPI()
        kpi.compute_and_check(ScenarioResult("x"))
        assert math.isnan(kpi.value)

    def test_inf_kpi_raises_kpi_error(self):
        # inf is a valid float; check it doesn't crash compute_and_check
        import math

        kpi = InfKPI()
        kpi.compute_and_check(ScenarioResult("x"))
        assert math.isinf(kpi.value)

    def test_negative_kpi(self):
        kpi = NegativeKPI()
        kpi.compute_and_check(ScenarioResult("x"))
        assert kpi.value == -42.0

    def test_zero_at_threshold_success(self):
        kpi = ZeroAtThresholdKPI()
        kpi.compute_and_check(ScenarioResult("x"))
        assert kpi.value == 0.0
        # threshold is 1e-6 (not 0.0, which would be falsy in the framework)
        assert kpi.success is True

    def test_raising_kpi_raises_kpi_error(self):
        kpi = RaisingKPI()
        with pytest.raises(KpiError):
            kpi.compute_and_check(ScenarioResult("x"))


# ---------------------------------------------------------------------------
# Data directories — #145
# ---------------------------------------------------------------------------


class TestDataDirectories:
    """Behavior tests for tiny and empty session shapes.

    Previously asserted on bundled subfolders under ``example/data/``; now
    constructed on ``tmp_path`` so the test exercises actual ETL/discovery
    behavior rather than the presence of checked-in fixture directories.
    """

    def test_tiny_dataset_etls_through_example_factory(self, tmp_path):
        from algomancy_data import CSVFile
        from example.data_handling.factories import ExampleETLFactory
        from example.data_handling.schemas import example_schemas

        dataset_dir = tmp_path / "tiny_session" / "tiny_data"
        dataset_dir.mkdir(parents=True)
        (dataset_dir / "sku_data.csv").write_text(
            "itemid;sku;description;category;daily_picks;volume_cm3;weight_kg;currentslot\n"
            "I1;SKU-1;Item one;A;10;1.0;0.5;SLOT-1\n",
            encoding="utf-8",
        )
        (dataset_dir / "warehouse_layout.csv").write_text(
            "slotid;x;y;zone\nSLOT-1;0.0;0.0;Z1\n",
            encoding="utf-8",
        )

        factory = ExampleETLFactory(schemas=example_schemas)
        files = {
            "sku_data": CSVFile(
                name="sku_data", path=str(dataset_dir / "sku_data.csv")
            ),
            "warehouse_layout": CSVFile(
                name="warehouse_layout",
                path=str(dataset_dir / "warehouse_layout.csv"),
            ),
        }
        result = factory.build_pipeline("tiny_data", files).run()

        assert result.is_success
        assert set(result.datasource.tables) == {"sku_data", "warehouse_layout"}
        assert len(result.datasource.tables["sku_data"]) == 1
        assert len(result.datasource.tables["warehouse_layout"]) == 1

    def test_empty_session_folder_is_discoverable(self, tmp_path):
        from algomancy_scenario.sessionmanager import SessionManager

        (tmp_path / "empty_session").mkdir()
        discovered = SessionManager._determine_sessions_from_folder(str(tmp_path))
        assert "empty_session" in discovered
