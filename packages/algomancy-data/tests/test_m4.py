"""Tests for the M4 ETL boilerplate reductions."""

from __future__ import annotations

import pytest

from algomancy_data import (
    Column,
    CSVFile,
    CSVSingleExtractor,
    DataSource,
    DataType,
    ETLConstructionError,
    FileExtension,
    JSONSingleExtractor,
    PrimaryKeyValidator,
    RequiredColumnsValidator,
    Schema,
    SchemaValidator,
    SimpleETLFactory,
    StatelessDataManager,
    XLSXMultiExtractor,
    XLSXSingleExtractor,
    get_extractor_class,
    registered_keys,
)
from algomancy_data.schema import SchemaType


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #


class WidgetSchema(Schema):
    _FILENAME = "widget"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column(name="id", dtype=DataType.STRING, primary_key=True)
    NAME = Column(name="name", dtype=DataType.STRING)
    PRICE = Column(name="price", dtype=DataType.FLOAT)


class SettingsSchema(Schema):
    _FILENAME = "settings"
    _EXTENSION = FileExtension.JSON
    _SCHEMA_TYPE = SchemaType.SINGLE

    KEY = Column(name="key", dtype=DataType.STRING)
    VALUE = Column(name="value", dtype=DataType.STRING)


class NoPKSchema(Schema):
    _FILENAME = "nopk"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    A = Column(name="a", dtype=DataType.STRING)


def _csv(tmp_path, rows="id;name;price\nw1;A;1.0\n"):
    p = tmp_path / "widget.csv"
    p.write_text(rows, encoding="utf-8")
    return CSVFile(name="widget", path=str(p))


# ------------------------------------------------------------------ #
# Issue #92 — registry shipped pre-populated
# ------------------------------------------------------------------ #


class TestRegistry:
    def test_csv_single_registered(self):
        assert (
            get_extractor_class(FileExtension.CSV, SchemaType.SINGLE)
            is CSVSingleExtractor
        )

    def test_json_single_registered(self):
        assert (
            get_extractor_class(FileExtension.JSON, SchemaType.SINGLE)
            is JSONSingleExtractor
        )

    def test_xlsx_single_registered(self):
        assert (
            get_extractor_class(FileExtension.XLSX, SchemaType.SINGLE)
            is XLSXSingleExtractor
        )

    def test_xlsx_multi_registered(self):
        assert (
            get_extractor_class(FileExtension.XLSX, SchemaType.MULTI)
            is XLSXMultiExtractor
        )

    def test_json_multi_registered(self):
        from algomancy_data.extractor import JSONMultiExtractor

        assert (
            get_extractor_class(FileExtension.JSON, SchemaType.MULTI)
            is JSONMultiExtractor
        )

    def test_unregistered_returns_none(self):
        # CSV multi has no built-in (and is unlikely to ever gain one).
        assert get_extractor_class(FileExtension.CSV, SchemaType.MULTI) is None

    def test_registered_keys_contains_defaults(self):
        keys = registered_keys()
        assert (FileExtension.CSV, SchemaType.SINGLE) in keys
        assert (FileExtension.XLSX, SchemaType.MULTI) in keys


# ------------------------------------------------------------------ #
# Issue #93 — default ETLFactory.create_extraction_sequence
# ------------------------------------------------------------------ #


class TestDefaultExtractionSequence:
    def test_default_uses_registry(self, tmp_path):
        factory = SimpleETLFactory([WidgetSchema])
        seq = factory.create_extraction_sequence({"widget": _csv(tmp_path)})
        assert len(seq._extractors) == 1
        assert isinstance(seq._extractors[0], CSVSingleExtractor)

    def test_unregistered_extension_raises(self, tmp_path):
        class WeirdSchema(Schema):
            _FILENAME = "weird"
            _EXTENSION = FileExtension.CSV
            _SCHEMA_TYPE = SchemaType.MULTI  # no extractor registered

            _DATATYPES = {"a": {"x": DataType.STRING}}

        factory = SimpleETLFactory([WeirdSchema])
        # Provide a CSV file-like to satisfy schemas_dct lookup
        csv_path = tmp_path / "weird.csv"
        csv_path.write_text("x\n1\n", encoding="utf-8")
        from algomancy_data import CSVFile

        file = CSVFile(name="weird", path=str(csv_path))
        with pytest.raises(ETLConstructionError, match="No extractor registered"):
            factory.create_extraction_sequence({"weird": file})


# ------------------------------------------------------------------ #
# Issue #94 — default validation sequence
# ------------------------------------------------------------------ #


class TestDefaultValidationSequence:
    def test_includes_required_and_schema_validators(self):
        factory = SimpleETLFactory([WidgetSchema])
        seq = factory.create_validation_sequence()
        v_types = [type(v) for v in seq._validators]
        assert RequiredColumnsValidator in v_types
        assert SchemaValidator in v_types

    def test_pk_validator_always_present(self):
        # Per issue #172: the validator is now appended unconditionally so
        # MULTI schemas (whose primary_key() raises TypeError) don't break
        # construction. PrimaryKeyValidator self-skips per-table when no
        # PK is declared, so its presence is harmless for NoPK schemas.
        for schema in (WidgetSchema, NoPKSchema):
            seq = SimpleETLFactory([schema]).create_validation_sequence()
            assert PrimaryKeyValidator in [type(v) for v in seq._validators]

    def test_pk_validator_self_skips_when_no_pk(self):
        # NoPKSchema has no primary_key declared. Running validation against
        # an empty data dict should produce no PK-related messages — the
        # validator iterates _schema_table_map and short-circuits per table.
        seq = SimpleETLFactory([NoPKSchema]).create_validation_sequence()
        result = seq.run_validation({})
        assert all(m.code != "MISSING_PK_COLUMN" for m in result.messages)
        assert all(m.code != "PK_NULL" for m in result.messages)


# ------------------------------------------------------------------ #
# Issue #95 — SimpleETLFactory zero-subclass usage
# ------------------------------------------------------------------ #


class TestSimpleETLFactory:
    def test_runs_pipeline_without_subclassing(self, tmp_path):
        factory = SimpleETLFactory([WidgetSchema])
        result = factory.build_pipeline(
            "widgets", {"widget": _csv(tmp_path)}, None
        ).run()
        assert result.is_success
        assert isinstance(result.datasource, DataSource)


# ------------------------------------------------------------------ #
# Issue #96 — prepare_files dispatches by schema-declared extension
# ------------------------------------------------------------------ #


class TestPrepareFilesBySchemaExtension:
    def _make_dm(self, schemas):
        return StatelessDataManager(
            etl_factory=SimpleETLFactory,
            schemas=schemas,
            save_type="json",
            data_object_type=DataSource,
            logger=None,
        )

    def test_dispatch_via_schema_when_extension_absent_in_path(self, tmp_path):
        # File name has no .csv suffix but the schema declares CSV.
        unusual = tmp_path / "widget"
        unusual.write_text("id;name;price\nw1;A;1.0\n", encoding="utf-8")
        dm = self._make_dm([WidgetSchema])
        files = dm.prepare_files(file_items_with_path=[("widget", str(unusual))])
        assert "widget" in files
        assert isinstance(files["widget"], CSVFile)

    def test_dispatch_via_schema_overrides_string_inference(self, tmp_path):
        # File name uses .json but schema says CSV. Schema wins.
        wrong_suffix = tmp_path / "widget.json"
        wrong_suffix.write_text("id;name;price\nw1;A;1.0\n", encoding="utf-8")
        dm = self._make_dm([WidgetSchema])
        files = dm.prepare_files(file_items_with_path=[("widget", str(wrong_suffix))])
        assert isinstance(files["widget"], CSVFile)

    def test_extension_falls_back_to_path_when_no_schema(self, tmp_path):
        # No matching schema → fall back to the path suffix.
        p = tmp_path / "thing.csv"
        p.write_text("a;b\n1;2\n", encoding="utf-8")
        dm = self._make_dm([WidgetSchema])  # mismatched name
        files = dm.prepare_files(file_items_with_path=[("thing", str(p))])
        assert isinstance(files["thing"], CSVFile)
