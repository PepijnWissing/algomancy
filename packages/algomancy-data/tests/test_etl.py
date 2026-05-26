"""Tests for predictable ETL termination (M3)."""

from __future__ import annotations

from typing import Dict

import pandas as pd
import pytest

from algomancy_data import (
    Column,
    CSVSingleExtractor,
    DataSource,
    DataSourceLoader,
    DataType,
    ETLFactory,
    ETLResult,
    FileExtension,
    NoopTransformer,
    PrimaryKeyValidator,
    RequiredColumnsValidator,
    Schema,
    SchemaValidator,
    StatefulDataManager,
    Transformer,
    ValidationSequence,
    ValidationSeverity,
)
from algomancy_data.extractor import ExtractionSequence
from algomancy_data.file import CSVFile
from algomancy_data.schema import SchemaType
from algomancy_data.transformer import TransformationSequence, fill_empty


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


class _GoodETLFactory(ETLFactory):
    """Factory that produces a passing pipeline for in-memory ``files``."""

    def create_extraction_sequence(self, files):
        return ExtractionSequence(
            extractors=[CSVSingleExtractor(files[name], WidgetSchema) for name in files]
        )

    def create_validation_sequence(self):
        return ValidationSequence(
            [
                RequiredColumnsValidator([WidgetSchema]),
                PrimaryKeyValidator([WidgetSchema]),
                SchemaValidator([WidgetSchema]),
            ]
        )

    def create_transformation_sequence(self):
        return TransformationSequence([NoopTransformer()])

    def create_loader(self):
        return DataSourceLoader(logger=None)


def _csv_file(
    tmp_path,
    rows: str = "id;name;price\nw1;Widget A;1.5\nw2;Widget B;2.0\n",
) -> CSVFile:
    """Write the rows to a temp CSV and return a path-backed ``CSVFile``."""
    path = tmp_path / "widget.csv"
    path.write_text(rows, encoding="utf-8")
    return CSVFile(name="widget", path=str(path))


# ------------------------------------------------------------------ #
# Issue #86 — ETLPipeline.run() returns ETLResult
# ------------------------------------------------------------------ #


class TestETLResult:
    def test_success_returns_etl_result(self, tmp_path):
        factory = _GoodETLFactory([WidgetSchema], None)
        pipeline = factory.build_pipeline(
            "widgets", {"widget": _csv_file(tmp_path)}, None
        )
        result = pipeline.run()
        assert isinstance(result, ETLResult)
        assert result.status == "success"
        assert result.is_success
        assert isinstance(result.datasource, DataSource)
        assert result.raised is None

    def test_validation_failure_returns_failed(self, tmp_path):
        # PK duplicates → PrimaryKeyValidator emits ERROR. We bump halt_on to
        # ERROR so the pipeline fails instead of letting them slide.
        class StrictFactory(_GoodETLFactory):
            def create_validation_sequence(self):
                return ValidationSequence(
                    [
                        RequiredColumnsValidator([WidgetSchema]),
                        PrimaryKeyValidator([WidgetSchema]),
                    ],
                    halt_on=ValidationSeverity.ERROR,
                )

        bad = "id;name;price\nw1;A;1.0\nw1;B;2.0\n"  # duplicate PK
        factory = StrictFactory([WidgetSchema], None)
        result = factory.build_pipeline(
            "widgets", {"widget": _csv_file(tmp_path, bad)}, None
        ).run()
        assert result.is_failure
        assert result.datasource is None
        assert any(m.code == "PK_DUPLICATE" for m in result.messages)


# ------------------------------------------------------------------ #
# Issue #87 — expected ETL errors as ETLResult(failed)
# ------------------------------------------------------------------ #


class TestExpectedErrors:
    def test_missing_file(self, tmp_path):
        # CSVFile reads content eagerly when path is given. So construct via
        # raw extractor with a CSVFile that never had a real path.
        from algomancy_data.file import CSVFile as _CSVFile

        missing_path = tmp_path / "does_not_exist.csv"

        class MissingExtractor(CSVSingleExtractor):
            def __init__(self):
                # bypass File constructor (which would raise on the path)
                file = _CSVFile.__new__(_CSVFile)
                file.name = "widget"
                file.path = str(missing_path)
                file.extension = FileExtension.CSV
                file.content = None
                super().__init__(file, WidgetSchema)

            def _extract_file(self):
                raise FileNotFoundError(f"missing: {missing_path}")

        class MissingFactory(_GoodETLFactory):
            def create_extraction_sequence(self, files):
                return ExtractionSequence(extractors=[MissingExtractor()])

        factory = MissingFactory([WidgetSchema], None)
        pipeline = factory.build_pipeline("widgets", {}, None)
        result = pipeline.run()
        assert result.is_failure
        assert isinstance(result.raised, FileNotFoundError)
        assert result.validation_result is not None
        assert any(m.code == "EXTRACTION_FAILED" for m in result.messages)

    def test_malformed_csv_routed_to_messages(self, tmp_path):
        bad = "id;name;price\nw1;A;not-a-number\nw2;B;also-bad\n"
        factory = _GoodETLFactory([WidgetSchema], None)
        result = factory.build_pipeline(
            "widgets", {"widget": _csv_file(tmp_path, bad)}, None
        ).run()
        assert any(m.code == "CONVERSION_FAILED" for m in result.messages)


# ------------------------------------------------------------------ #
# Issue #88 — programmer errors propagate
# ------------------------------------------------------------------ #


class _BuggyTransformer(Transformer):
    def __init__(self):
        super().__init__(name="buggy")

    def transform(self, data: Dict[str, pd.DataFrame]) -> None:
        raise KeyError("intentional bug")


class TestProgrammerErrors:
    def test_keyerror_in_transformer_propagates(self, tmp_path):
        class BuggyFactory(_GoodETLFactory):
            def create_transformation_sequence(self):
                return TransformationSequence([_BuggyTransformer()])

        factory = BuggyFactory([WidgetSchema], None)
        pipeline = factory.build_pipeline(
            "widgets", {"widget": _csv_file(tmp_path)}, None
        )
        with pytest.raises(KeyError, match="intentional bug"):
            pipeline.run()

    def test_attributeerror_propagates(self, tmp_path):
        class AEFactory(_GoodETLFactory):
            def create_transformation_sequence(self):
                class AETransformer(Transformer):
                    def __init__(self):
                        super().__init__(name="ae")

                    def transform(self, data):
                        data["x"].nonexistent_attribute  # noqa: B018

                return TransformationSequence([AETransformer()])

        factory = AEFactory([WidgetSchema], None)
        with pytest.raises((AttributeError, KeyError)):
            factory.build_pipeline(
                "widgets", {"widget": _csv_file(tmp_path)}, None
            ).run()


# ------------------------------------------------------------------ #
# Issue #89 — DataTypeConverter routes failures via validation messages
# ------------------------------------------------------------------ #


class TestConversionMessages:
    def test_conversion_failure_no_silent_nans(self, tmp_path):
        bad = "id;name;price\nw1;A;abc\n"
        factory = _GoodETLFactory([WidgetSchema], None)
        result = factory.build_pipeline(
            "widgets", {"widget": _csv_file(tmp_path, bad)}, None
        ).run()
        conv = [m for m in result.messages if m.code == "CONVERSION_FAILED"]
        assert conv, "expected a CONVERSION_FAILED validation message"
        assert conv[0].column == "price"
        assert conv[0].table == "widget"


# ------------------------------------------------------------------ #
# Issue #90 — fill_empty no longer uses deprecated kwarg
# ------------------------------------------------------------------ #


class TestFillEmpty:
    def test_no_future_warning(self, recwarn):
        df = pd.DataFrame({"a": [1, None, 3], "b": [None, 2, None]})
        out = fill_empty(df)
        # Should not emit FutureWarning about fillna(method=...)
        future_warnings = [w for w in recwarn.list if w.category is FutureWarning]
        assert future_warnings == []
        # ffill axis=1: forward-fill across columns within each row
        assert out.iloc[0, 1] == 1  # a=1 carried forward into b
        assert out.iloc[1, 0] is None or pd.isna(out.iloc[1, 0])


# ------------------------------------------------------------------ #
# Issue #91 — StatefulDataManager.startup partial-state safety
# ------------------------------------------------------------------ #


class TestStatefulStartup:
    def test_corrupt_file_is_skipped_and_recorded(self, tmp_path):
        # Drop a non-parseable .json into the data folder.
        data_folder = tmp_path / "data"
        data_folder.mkdir()
        bad = data_folder / "broken.json"
        bad.write_text("not valid json", encoding="utf-8")

        class _NoopETL(ETLFactory):
            def create_extraction_sequence(self, files):
                return ExtractionSequence()

            def create_validation_sequence(self):
                return ValidationSequence()

            def create_transformation_sequence(self):
                return TransformationSequence()

            def create_loader(self):
                return DataSourceLoader(logger=None)

        dm = StatefulDataManager(
            etl_factory=_NoopETL,
            schemas=[WidgetSchema],
            data_folder=str(data_folder),
            save_type="json",
            data_object_type=DataSource,
            logger=None,
        )
        # Should not raise; broken file should land in startup_errors.
        dm.startup()
        assert len(dm.startup_errors) == 1
        assert "broken.json" in dm.startup_errors[0][0]
        # Manager left in a defined state (no partial keys).
        assert dm.get_data_keys() == []


# ------------------------------------------------------------------ #
# ETLResult convenience helpers
# ------------------------------------------------------------------ #


class TestETLResultHelpers:
    def test_messages_accessor(self):
        result = ETLResult(status="failed", validation_result=None)
        assert result.messages == []
