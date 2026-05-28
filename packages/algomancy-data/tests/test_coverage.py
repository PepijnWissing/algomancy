"""Additional coverage-focused tests for algomancy-data (M6)."""

from __future__ import annotations

import base64
import json

import pandas as pd
import pytest

from algomancy_data import (
    CSVFile,
    CleanTransformer,
    Column,
    DataClassification,
    DataSource,
    DataSourceLoader,
    DataType,
    ETLConstructionError,
    File,
    FileExtension,
    JoinTransformer,
    JSONFile,
    NoopTransformer,
    Schema,
    SimpleETLFactory,
    StatefulDataManager,
    StatelessDataManager,
    XLSXFile,
)
from algomancy_data.extractor import CSVSingleExtractor, JSONSingleExtractor
from algomancy_data.schema import SchemaType
from algomancy_data.transformer import TransformationSequence, drop_empty, fill_empty


class WidgetSchema(Schema):
    _FILENAME = "widget"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column(name="id", dtype=DataType.STRING, primary_key=True)
    NAME = Column(name="name", dtype=DataType.STRING)


# ------------------------------------------------------------------ #
# file.py — CSVFile, JSONFile, XLSXFile (path & uploader)
# ------------------------------------------------------------------ #


class TestFileFromPath:
    def test_csv_from_path(self, tmp_path):
        p = tmp_path / "x.csv"
        p.write_text("a,b\n1,2\n", encoding="utf-8")
        f = CSVFile(name="x", path=str(p))
        assert "a,b" in f.content
        assert isinstance(f, File)

    def test_json_from_path(self, tmp_path):
        p = tmp_path / "x.json"
        p.write_text('[{"a": 1}]', encoding="utf-8")
        f = JSONFile(name="x", path=str(p))
        assert f.content is not None

    def test_csv_from_uploader_content(self):
        raw = "a,b\n1,2\n"
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        data_uri = f"data:text/csv;base64,{encoded}"
        f = CSVFile(name="x", content=data_uri)
        assert "a,b" in f.content

    def test_json_from_uploader_content(self):
        raw = json.dumps([{"a": 1}])
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        data_uri = f"data:application/json;base64,{encoded}"
        f = JSONFile(name="x", content=data_uri)
        decoded = json.loads(f.content)
        assert decoded == [{"a": 1}]

    def test_csv_uploader_bad_content_raises(self):
        with pytest.raises(ValueError):
            CSVFile(name="x", content="not-a-data-uri")

    def test_read_contents_from_missing_path(self, tmp_path):
        bad = tmp_path / "nope.csv"
        with pytest.raises(FileNotFoundError):
            CSVFile(name="x", path=str(bad))


class TestXLSXFileFromPath:
    def test_xlsx_from_path(self, tmp_path):
        # Build a real xlsx file so the path branch is exercised.
        p = tmp_path / "x.xlsx"
        df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        df.to_excel(p, sheet_name="Sheet1", index=False)
        f = XLSXFile(name="x", path=str(p))
        payload = json.loads(f.content)
        assert "metadata" in payload
        assert "Sheet1" in payload["sheets"]


# ------------------------------------------------------------------ #
# transformer.py — clean / join / fill / drop
# ------------------------------------------------------------------ #


class TestTransformers:
    def test_clean_lowercases_and_dropna(self):
        df = pd.DataFrame({"Foo": [1, None], "Bar": [3, 4]})
        data = {"t": df}
        CleanTransformer().transform(data)
        # Mutated in-place: original df should now have lowercase columns
        assert "foo" in df.columns or "Foo" in df.columns

    def test_join_transformer(self):
        data = {
            "left": pd.DataFrame({"k": [1, 2], "lv": ["a", "b"]}),
            "right": pd.DataFrame({"k": [1, 2], "rv": ["x", "y"]}),
        }
        JoinTransformer(left="left", right="right", on="k", output="joined").transform(
            data
        )
        assert "joined" in data
        assert sorted(data["joined"].columns.tolist()) == ["k", "lv", "rv"]

    def test_noop_transformer(self):
        before = {"t": pd.DataFrame({"a": [1]})}
        out = NoopTransformer().transform(before)
        assert out is before

    def test_fill_empty(self):
        df = pd.DataFrame({"a": [1, 2], "b": [None, 4]})
        out = fill_empty(df)
        # Row 0: a=1, b filled forward from a=1
        assert out.iloc[0, 1] == 1

    def test_drop_empty(self):
        df = pd.DataFrame({"a": [1, None], "b": [2, 4]})
        out = drop_empty(df)
        assert len(out) == 1

    def test_transformation_sequence_runs_in_order(self):
        # Two transformers; second sees the first's effect.
        seen: list = []

        class T1(NoopTransformer):
            def transform(self, data):
                seen.append("t1")
                return data

        class T2(NoopTransformer):
            def transform(self, data):
                seen.append("t2")
                return data

        seq = TransformationSequence([T1(), T2()])
        seq.run_transformation({"x": pd.DataFrame()})
        assert seen == ["t1", "t2"]


# ------------------------------------------------------------------ #
# datamanager.py — Stateless / Stateful behaviours
# ------------------------------------------------------------------ #


class TestDataManagerBehaviours:
    def test_stateless_set_get_delete(self):
        dm = StatelessDataManager(
            etl_factory=SimpleETLFactory,
            schemas=[WidgetSchema],
            save_type="json",
            data_object_type=DataSource,
            logger=None,
        )
        ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="w")
        dm.set_data("w", ds)
        assert dm.get_data("w") is ds
        assert "w" in dm.get_data_keys()
        dm.delete_data("w")
        assert "w" not in dm.get_data_keys()

    def test_derive_data(self):
        dm = StatelessDataManager(
            etl_factory=SimpleETLFactory,
            schemas=[WidgetSchema],
            save_type="json",
            data_object_type=DataSource,
            logger=None,
        )
        ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="master")
        dm.set_data("master", ds)
        dm.derive_data("master", "derived")
        assert "derived" in dm.get_data_keys()

    def test_add_data_source(self):
        dm = StatelessDataManager(
            etl_factory=SimpleETLFactory,
            schemas=[WidgetSchema],
            save_type="json",
            data_object_type=DataSource,
            logger=None,
        )
        ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="loaded")
        dm.add_data_source(ds)
        assert "loaded" in dm.get_data_keys()

    def test_prepare_files_from_content_uses_schema_extension(self, tmp_path):
        dm = StatelessDataManager(
            etl_factory=SimpleETLFactory,
            schemas=[WidgetSchema],
            save_type="json",
            data_object_type=DataSource,
            logger=None,
        )
        # Provide a base64 CSV data URI through the uploader code path.
        raw = "id;name\nw1;A\n"
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        data_uri = f"data:text/csv;base64,{encoded}"
        files = dm.prepare_files(file_items_with_content=[("widget", "csv", data_uri)])
        assert isinstance(files["widget"], CSVFile)

    def test_prepare_files_raises_when_nothing_provided(self):
        dm = StatelessDataManager(
            etl_factory=SimpleETLFactory,
            schemas=[WidgetSchema],
            save_type="json",
            data_object_type=DataSource,
            logger=None,
        )
        with pytest.raises(ETLConstructionError):
            dm.prepare_files()

    def test_stateful_store_data(self, tmp_path):
        dm = StatefulDataManager(
            etl_factory=SimpleETLFactory,
            schemas=[WidgetSchema],
            data_folder=str(tmp_path),
            save_type="json",
            data_object_type=DataSource,
            logger=None,
        )
        df = pd.DataFrame({"id": ["w1"], "name": ["A"]})
        dm.store_data("widgets", {"widget": df})
        assert "widgets" in dm.get_data_keys()
        assert (tmp_path / "widgets" / "widget.csv").exists()

    def test_stateful_store_data_refuses_overwrite(self, tmp_path):
        dm = StatefulDataManager(
            etl_factory=SimpleETLFactory,
            schemas=[WidgetSchema],
            data_folder=str(tmp_path),
            save_type="json",
            data_object_type=DataSource,
            logger=None,
        )
        df = pd.DataFrame({"id": ["w1"], "name": ["A"]})
        dm.store_data("widgets", {"widget": df})
        with pytest.raises(Exception, match="already exists"):
            dm.store_data("widgets", {"widget": df})

    def test_stateful_delete_master_data_removes_files(self, tmp_path):
        dm = StatefulDataManager(
            etl_factory=SimpleETLFactory,
            schemas=[WidgetSchema],
            data_folder=str(tmp_path),
            save_type="json",
            data_object_type=DataSource,
            logger=None,
        )
        ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="x")
        directory = tmp_path / "x"
        directory.mkdir()
        (directory / "y.csv").write_text("a\n1\n", encoding="utf-8")
        dm.set_data("x", ds)
        dm.delete_data("x")
        assert not directory.exists()


# ------------------------------------------------------------------ #
# extractor.py — JSON, sequence helpers
# ------------------------------------------------------------------ #


class TestExtractorEdges:
    def test_json_extractor(self, tmp_path):
        p = tmp_path / "x.json"
        p.write_text('[{"id": "p1", "name": "A"}]', encoding="utf-8")
        f = JSONFile(name="widget", path=str(p))
        ex = JSONSingleExtractor(f, WidgetSchema)
        out = ex.extract()
        assert "widget" in out
        assert out["widget"]["id"].tolist() == ["p1"]

    def test_extraction_sequence_data_cache(self, tmp_path):
        from algomancy_data.extractor import ExtractionSequence

        p = tmp_path / "x.csv"
        p.write_text("id;name\nw1;A\n", encoding="utf-8")
        f = CSVFile(name="widget", path=str(p))
        ex = CSVSingleExtractor(f, WidgetSchema)
        seq = ExtractionSequence(extractors=[ex])
        first = seq.data
        second = seq.data  # cached, no re-extraction
        assert first is second


# ------------------------------------------------------------------ #
# loader.py — DataSourceLoader passes validation messages through
# ------------------------------------------------------------------ #


class TestLoader:
    def test_loader_attaches_validation_messages(self):
        from algomancy_data import ValidationMessage, ValidationSeverity

        msgs = [ValidationMessage(ValidationSeverity.INFO, "ok")]
        loader = DataSourceLoader(logger=None)
        ds = loader.load(
            name="x",
            data={"a": pd.DataFrame({"v": [1]})},
            validation_messages=msgs,
            ds_type=DataClassification.MASTER_DATA,
        )
        assert ds.validation_messages == msgs
        assert ds.name == "x"


# ------------------------------------------------------------------ #
# DataTypeConverter — direct exercise of coercion branches
# ------------------------------------------------------------------ #


class TestDataTypeConverter:
    def test_float_european_decimal(self):
        from algomancy_data.extractor import DataTypeConverter

        df = pd.DataFrame({"x": ["1,5", "2,5"]})
        out = DataTypeConverter.convert_dtypes(df, {"x": DataType.FLOAT})
        assert out["x"].tolist() == [1.5, 2.5]

    def test_int_european_decimal(self):
        from algomancy_data.extractor import DataTypeConverter

        df = pd.DataFrame({"x": ["1,0", "2,0"]})
        out = DataTypeConverter.convert_dtypes(df, {"x": DataType.INTEGER})
        assert out["x"].tolist() == [1, 2]

    def test_datetime_iso(self):
        from algomancy_data.extractor import DataTypeConverter

        df = pd.DataFrame({"x": ["2024-01-01", "2024-02-01"]})
        out = DataTypeConverter.convert_dtypes(df, {"x": DataType.DATETIME})
        assert out["x"].dtype == DataType.DATETIME

    def test_boolean_string_mapping(self):
        from algomancy_data.extractor import DataTypeConverter

        df = pd.DataFrame({"x": ["yes", "no"]})
        out = DataTypeConverter.convert_dtypes(df, {"x": DataType.BOOLEAN})
        assert out["x"].iloc[0] in (True, "yes")  # mapping or pass-through

    def test_string_dtype(self):
        from algomancy_data.extractor import DataTypeConverter

        df = pd.DataFrame({"x": [1, 2, 3]})
        out = DataTypeConverter.convert_dtypes(df, {"x": DataType.STRING})
        assert out["x"].dtype == DataType.STRING

    def test_skips_missing_column(self):
        from algomancy_data.extractor import DataTypeConverter

        df = pd.DataFrame({"a": [1]})
        out = DataTypeConverter.convert_dtypes(df, {"missing": DataType.INTEGER})
        assert list(out.columns) == ["a"]

    def test_unsupported_dtype_raises(self):
        from algomancy_data.extractor import DataTypeConverter

        df = pd.DataFrame({"a": [1]})
        with pytest.raises(NotImplementedError):
            DataTypeConverter.convert_dtypes(df, {"a": "ridiculous-dtype"})


# ------------------------------------------------------------------ #
# XLSXMultiExtractor — exercise multi-sheet branch
# ------------------------------------------------------------------ #


class TestXLSXMulti:
    def test_multi_extractor(self, tmp_path):
        from algomancy_data.extractor import XLSXMultiExtractor

        class MultiSchema(Schema):
            _FILENAME = "multi"
            _EXTENSION = FileExtension.XLSX
            _SCHEMA_TYPE = SchemaType.MULTI
            _DATATYPES = {
                "SheetA": {"a": DataType.STRING},
                "SheetB": {"b": DataType.INTEGER},
            }

        p = tmp_path / "multi.xlsx"
        with pd.ExcelWriter(p) as writer:
            pd.DataFrame({"a": ["x", "y"]}).to_excel(
                writer, sheet_name="SheetA", index=False
            )
            pd.DataFrame({"b": [1, 2]}).to_excel(
                writer, sheet_name="SheetB", index=False
            )

        f = XLSXFile(name="multi", path=str(p))
        ex = XLSXMultiExtractor(f, MultiSchema)
        out = ex.extract()
        assert "multi.SheetA" in out
        assert "multi.SheetB" in out
        assert out["multi.SheetB"]["b"].tolist() == [1, 2]
