"""Tests proving DatabaseDataManager works for arbitrary BaseDataSource subclasses.

Covers both persistence branches:

* A subclass that does NOT implement SqlTableLayout → JSON-blob fallback path.
* A subclass that DOES implement SqlTableLayout (without subclassing the
  bundled DataSource) → per-sub-table SQL storage.
"""

from __future__ import annotations

import json

import pytest

pytest.importorskip("sqlalchemy", reason="requires algomancy-data[database]")

import pandas as pd
import sqlalchemy as sa

from algomancy_data import (
    Column,
    CSVSingleExtractor,
    DataClassification,
    DataSourceLoader,
    DataType,
    ETLFactory,
    FileExtension,
    NoopTransformer,
    RequiredColumnsValidator,
    Schema,
    SchemaValidator,
    ValidationSequence,
)
from algomancy_data.database.database_manager import DatabaseDataManager
from algomancy_data.datasource import BaseDataSource
from algomancy_data.extractor import ExtractionSequence
from algomancy_data.schema import SchemaType
from algomancy_data.transformer import TransformationSequence


# ------------------------------------------------------------------ #
# Minimal schema + ETL factory (the ETL pipeline isn't exercised here,
# but DataManager.__init__ requires both)
# ------------------------------------------------------------------ #


class ItemSchema(Schema):
    _FILENAME = "item"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column(name="id", dtype=DataType.STRING, primary_key=True)


class SimpleETLFactory(ETLFactory):
    def create_extraction_sequence(self, files):
        return ExtractionSequence(
            extractors=[CSVSingleExtractor(files[name], ItemSchema) for name in files]
        )

    def create_validation_sequence(self):
        return ValidationSequence(
            [RequiredColumnsValidator([ItemSchema]), SchemaValidator([ItemSchema])]
        )

    def create_transformation_sequence(self):
        return TransformationSequence([NoopTransformer()])

    def create_loader(self):
        return DataSourceLoader(logger=None)


# ------------------------------------------------------------------ #
# JSON-blob subclass: no per-table state, no SqlTableLayout
# ------------------------------------------------------------------ #


class BlobDataSource(BaseDataSource):
    """A BaseDataSource subclass with non-tabular state.

    Holds a free-form ``payload`` dict — there are no DataFrames at all, so
    per-sub-table SQL storage is meaningless. This forces the JSON-blob path.
    """

    def __init__(
        self,
        ds_type: DataClassification,
        name: str = None,
        validation_messages=None,
        ds_id: str | None = None,
        creation_datetime=None,
        payload: dict | None = None,
    ) -> None:
        super().__init__(ds_type, name, validation_messages, ds_id, creation_datetime)
        self.payload: dict = payload if payload is not None else {}

    def to_json(self) -> str:
        return json.dumps(
            {
                "id": self.id,
                "name": self._name,
                "type": str(self._ds_type),
                "creation_datetime": str(self.creation_datetime),
                "payload": self.payload,
            }
        )

    @classmethod
    def from_json(cls, json_string: str) -> "BlobDataSource":
        d = json.loads(json_string)
        return cls(
            ds_type=DataClassification(d["type"]),
            name=d["name"],
            ds_id=d["id"],
            creation_datetime=d["creation_datetime"],
            payload=d["payload"],
        )


# ------------------------------------------------------------------ #
# Per-table SQL subclass that does NOT inherit from DataSource
# ------------------------------------------------------------------ #


class TabularDataSource(BaseDataSource):
    """A BaseDataSource subclass that opts into SqlTableLayout without
    inheriting from the bundled DataSource. Proves the per-table SQL path
    is driven by the protocol, not by the concrete class."""

    def __init__(
        self,
        ds_type: DataClassification,
        name: str = None,
        validation_messages=None,
        ds_id: str | None = None,
        creation_datetime=None,
    ) -> None:
        super().__init__(ds_type, name, validation_messages, ds_id, creation_datetime)
        self._tables: dict[str, pd.DataFrame] = {}

    def to_sql_tables(self) -> dict[str, pd.DataFrame]:
        return self._tables

    def from_sql_tables(self, tables: dict[str, pd.DataFrame]) -> None:
        self._tables.update(tables)

    def to_json(self) -> str:  # required by abstract API, used by derive()
        return json.dumps(
            {
                "id": self.id,
                "name": self._name,
                "type": str(self._ds_type),
                "creation_datetime": str(self.creation_datetime),
                "tables": {
                    n: df.to_dict(orient="records") for n, df in self._tables.items()
                },
            }
        )

    @classmethod
    def from_json(cls, json_string: str) -> "TabularDataSource":
        d = json.loads(json_string)
        ds = cls(
            ds_type=DataClassification(d["type"]),
            name=d["name"],
            ds_id=d["id"],
            creation_datetime=d["creation_datetime"],
        )
        ds.from_sql_tables(
            {n: pd.DataFrame(records) for n, records in d["tables"].items()}
        )
        return ds


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #


@pytest.fixture
def engine():
    return sa.create_engine("sqlite:///:memory:")


def _make_manager(engine, data_object_type):
    m = DatabaseDataManager(
        etl_factory=SimpleETLFactory,
        schemas=[ItemSchema()],
        engine=engine,
        session_id="test",
        data_object_type=data_object_type,
    )
    m.startup()
    return m


# ------------------------------------------------------------------ #
# Tests
# ------------------------------------------------------------------ #


class TestJsonBlobFallback:
    def test_subclass_without_sql_layout_uses_json_payload(self, engine):
        m = _make_manager(engine, BlobDataSource)
        ds = BlobDataSource(
            ds_type=DataClassification.MASTER_DATA,
            name="blob",
            payload={"alpha": 1, "beta": ["two", "three"]},
        )
        m.add_data_source(ds)

        # Catalogue row carries the JSON payload; no shared algomancy_ds__... tables.
        inspector = sa.inspect(engine)
        data_tables = [
            t for t in inspector.get_table_names() if t.startswith("algomancy_ds__")
        ]
        assert data_tables == []
        assert m._db_catalogue["blob"]["payload"] is not None

    def test_round_trip_across_managers(self, engine):
        m1 = _make_manager(engine, BlobDataSource)
        original = BlobDataSource(
            ds_type=DataClassification.MASTER_DATA,
            name="blob",
            payload={"hello": "world", "count": 42},
        )
        m1.add_data_source(original)

        m2 = _make_manager(engine, BlobDataSource)
        loaded = m2.get_data("blob")

        assert isinstance(loaded, BlobDataSource)
        assert loaded.name == "blob"
        assert loaded.payload == {"hello": "world", "count": 42}

    def test_delete_removes_catalogue_row(self, engine):
        m = _make_manager(engine, BlobDataSource)
        ds = BlobDataSource(
            ds_type=DataClassification.MASTER_DATA, name="ephemeral", payload={"x": 1}
        )
        m.add_data_source(ds)

        m.delete_data("ephemeral")
        assert "ephemeral" not in m.get_data_keys()
        assert m.get_data("ephemeral") is None


class TestSqlLayoutCustomSubclass:
    """The per-sub-table SQL path must work for non-DataSource subclasses too."""

    def test_round_trip_writes_real_sql_tables(self, engine):
        m1 = _make_manager(engine, TabularDataSource)
        ds = TabularDataSource(ds_type=DataClassification.MASTER_DATA, name="tab")
        df = pd.DataFrame({"id": ["a", "b"], "v": [1, 2]})
        ds.from_sql_tables({"items": df})
        m1.add_data_source(ds)

        # A shared per-sub-table SQL table exists, and the payload column is NULL.
        inspector = sa.inspect(engine)
        assert "algomancy_ds__items" in inspector.get_table_names()
        assert m1._db_catalogue["tab"]["payload"] is None
        assert m1._db_catalogue["tab"]["sub_tables"] == ["items"]

        m2 = _make_manager(engine, TabularDataSource)
        loaded = m2.get_data("tab")
        assert isinstance(loaded, TabularDataSource)
        pd.testing.assert_frame_equal(
            loaded.to_sql_tables()["items"].reset_index(drop=True),
            df.reset_index(drop=True),
            check_dtype=False,
        )

    def test_mismatched_data_object_type_raises(self, engine):
        """Reading a per-table row with a subclass that doesn't satisfy
        SqlTableLayout must fail loudly, not silently return empty data."""
        # Persist via the per-table path.
        m_writer = _make_manager(engine, TabularDataSource)
        ds = TabularDataSource(ds_type=DataClassification.MASTER_DATA, name="tab")
        ds.from_sql_tables({"items": pd.DataFrame({"id": ["a"], "v": [1]})})
        m_writer.add_data_source(ds)

        # Reopen with a BlobDataSource data_object_type — it can't satisfy the protocol.
        m_reader = _make_manager(engine, BlobDataSource)
        with pytest.raises(TypeError, match="SqlTableLayout"):
            m_reader.get_data("tab")
