"""Tests for DatabaseDataManager — persistence round-trips via SQLite."""

from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy", reason="requires algomancy-data[database]")

import pandas as pd
import sqlalchemy as sa

from algomancy_data import (
    Column,
    CSVSingleExtractor,
    DataSource,
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
from algomancy_data.extractor import ExtractionSequence
from algomancy_data.file import CSVFile
from algomancy_data.schema import SchemaType
from algomancy_data.transformer import TransformationSequence


# ------------------------------------------------------------------ #
# Minimal test schema + ETL factory
# ------------------------------------------------------------------ #


class ItemSchema(Schema):
    _FILENAME = "item"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column(name="id", dtype=DataType.STRING, primary_key=True)
    NAME = Column(name="name", dtype=DataType.STRING)
    PRICE = Column(name="price", dtype=DataType.FLOAT)


class SimpleETLFactory(ETLFactory):
    @classmethod
    def create_extraction_sequence(cls, files=None, schemas=None, logger=None):
        return ExtractionSequence(
            extractors=[CSVSingleExtractor(files[name], ItemSchema) for name in files]
        )

    @classmethod
    def create_validation_sequence(cls, schemas=None, logger=None):
        return ValidationSequence(
            [RequiredColumnsValidator([ItemSchema]), SchemaValidator([ItemSchema])]
        )

    @classmethod
    def create_transformation_sequence(cls, schemas=None, logger=None):
        return TransformationSequence([NoopTransformer()])

    @classmethod
    def create_loader(cls, logger=None):
        return DataSourceLoader(logger=None)


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #


@pytest.fixture
def engine():
    return sa.create_engine("sqlite:///:memory:")


@pytest.fixture
def dm(engine):
    manager = DatabaseDataManager(
        etl_factory=SimpleETLFactory,
        schemas=[ItemSchema()],
        engine=engine,
        session_id="test",
        data_object_type=DataSource,
    )
    manager.startup()
    return manager


@pytest.fixture
def csv_item_file(tmp_path) -> CSVFile:
    path = tmp_path / "item.csv"
    path.write_text("id;name;price\na1;Bolt;0.5\na2;Nut;0.3\n", encoding="utf-8")
    return CSVFile(name="item", path=str(path))


# ------------------------------------------------------------------ #
# Tests
# ------------------------------------------------------------------ #


class TestDatabaseDataManagerStartup:
    def test_startup_creates_catalogue_table(self, engine):
        """Startup should create the algomancy_datasets table."""
        inspector = sa.inspect(engine)
        # Before startup the table should not exist
        assert "algomancy_datasets" not in inspector.get_table_names()
        dm = DatabaseDataManager(
            etl_factory=SimpleETLFactory,
            schemas=[ItemSchema()],
            engine=engine,
            session_id="s",
            data_object_type=DataSource,
        )
        dm.startup()
        assert "algomancy_datasets" in sa.inspect(engine).get_table_names()

    def test_startup_loads_existing_metadata(self, engine):
        """Startup on an existing DB loads previously persisted dataset keys."""
        # First session: ETL and persist
        dm1 = DatabaseDataManager(
            etl_factory=SimpleETLFactory,
            schemas=[ItemSchema()],
            engine=engine,
            session_id="s",
            data_object_type=DataSource,
        )
        dm1.startup()
        ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="items")
        ds.add_table("item", pd.DataFrame({"id": ["x"], "name": ["X"], "price": [1.0]}))
        dm1.add_data_source(ds)

        # Second session (simulated restart): startup should see the dataset
        dm2 = DatabaseDataManager(
            etl_factory=SimpleETLFactory,
            schemas=[ItemSchema()],
            engine=engine,
            session_id="s",
            data_object_type=DataSource,
        )
        dm2.startup()
        assert "items" in dm2.get_data_keys()


class TestDatabaseDataManagerRoundTrip:
    def test_add_and_get_data(self, dm):
        """add_data_source then get_data should return an equal DataSource."""
        ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="widgets")
        df = pd.DataFrame({"id": ["w1", "w2"], "name": ["A", "B"], "price": [1.5, 2.0]})
        ds.add_table("item", df)
        dm.add_data_source(ds)

        loaded = dm.get_data("widgets")
        assert loaded is not None
        assert loaded.name == "widgets"
        assert "item" in loaded.tables
        pd.testing.assert_frame_equal(
            loaded.tables["item"].reset_index(drop=True),
            df.reset_index(drop=True),
            check_dtype=False,
        )

    def test_lazy_loading(self, dm):
        """Data should be loaded from DB if not already in memory."""
        ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="lazy_ds")
        df = pd.DataFrame({"id": ["x"], "name": ["X"], "price": [9.9]})
        ds.add_table("item", df)
        dm.add_data_source(ds)

        # Clear the in-memory cache to simulate a lazy-load scenario
        dm._data.clear()
        assert "lazy_ds" in dm.get_data_keys()  # still known from catalogue
        loaded = dm.get_data("lazy_ds")
        assert loaded is not None
        assert loaded.tables["item"].iloc[0]["name"] == "X"

    def test_derive_data(self, dm):
        """derive_data should create a new DB-persisted dataset."""
        ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="src")
        df = pd.DataFrame({"id": ["a"], "name": ["Alpha"], "price": [5.0]})
        ds.add_table("item", df)
        dm.add_data_source(ds)

        dm.derive_data("src", "derived")
        assert "derived" in dm.get_data_keys()

        # Verify DB persistence by loading fresh from a cold cache
        dm._data.clear()
        derived = dm.get_data("derived")
        assert derived is not None
        assert derived.name == "derived"

    def test_delete_data(self, dm):
        """delete_data should remove from memory and DB."""
        ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="to_delete")
        ds.add_table("item", pd.DataFrame({"id": ["d"], "name": ["D"], "price": [0.0]}))
        dm.add_data_source(ds)

        assert "to_delete" in dm.get_data_keys()
        dm.delete_data("to_delete")
        assert "to_delete" not in dm.get_data_keys()
        assert dm.get_data("to_delete") is None

    def test_session_isolation(self, engine):
        """Two managers with different session_ids must not see each other's data."""
        for sid in ("session_a", "session_b"):
            m = DatabaseDataManager(
                etl_factory=SimpleETLFactory,
                schemas=[ItemSchema()],
                engine=engine,
                session_id=sid,
                data_object_type=DataSource,
            )
            m.startup()
            ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="shared_name")
            ds.add_table(
                "item", pd.DataFrame({"id": [sid], "name": [sid], "price": [1.0]})
            )
            m.add_data_source(ds)

        m_a = DatabaseDataManager(
            etl_factory=SimpleETLFactory,
            schemas=[ItemSchema()],
            engine=engine,
            session_id="session_a",
            data_object_type=DataSource,
        )
        m_a.startup()
        m_b = DatabaseDataManager(
            etl_factory=SimpleETLFactory,
            schemas=[ItemSchema()],
            engine=engine,
            session_id="session_b",
            data_object_type=DataSource,
        )
        m_b.startup()

        # Each manager sees its own data
        loaded_a = m_a.get_data("shared_name")
        loaded_b = m_b.get_data("shared_name")
        assert loaded_a.tables["item"].iloc[0]["id"] == "session_a"
        assert loaded_b.tables["item"].iloc[0]["id"] == "session_b"


class TestSharedTableLayout:
    def test_multiple_sessions_and_datasets_share_one_physical_table(self, engine):
        """Two sessions × two datasets should still write into a single
        ``algomancy_ds__item`` table — that's the whole point of the revision."""
        for sid in ("s1", "s2"):
            m = DatabaseDataManager(
                etl_factory=SimpleETLFactory,
                schemas=[ItemSchema()],
                engine=engine,
                session_id=sid,
                data_object_type=DataSource,
            )
            m.startup()
            for ds_name in ("alpha", "beta"):
                ds = DataSource(ds_type=DataClassification.MASTER_DATA, name=ds_name)
                ds.add_table(
                    "item",
                    pd.DataFrame(
                        {
                            "id": [f"{sid}-{ds_name}"],
                            "name": [ds_name],
                            "price": [1.0],
                        }
                    ),
                )
                m.add_data_source(ds)

        inspector = sa.inspect(engine)
        data_tables = [
            t for t in inspector.get_table_names() if t.startswith("algomancy_ds__")
        ]
        assert data_tables == ["algomancy_ds__item"], (
            f"Expected exactly one shared table, got {data_tables}"
        )

        # Four rows total: 2 sessions × 2 datasets.
        with engine.connect() as conn:
            row_count = conn.execute(
                sa.text("SELECT COUNT(*) FROM algomancy_ds__item")
            ).scalar()
        assert row_count == 4

    def test_overwriting_same_dataset_replaces_rows(self, dm):
        """Re-persisting the same (session, dataset_name) replaces its rows."""
        ds1 = DataSource(ds_type=DataClassification.MASTER_DATA, name="rep")
        ds1.add_table(
            "item", pd.DataFrame({"id": ["a"], "name": ["A"], "price": [1.0]})
        )
        dm.add_data_source(ds1)

        ds2 = DataSource(ds_type=DataClassification.DERIVED_DATA, name="rep")
        ds2.add_table(
            "item",
            pd.DataFrame({"id": ["x", "y"], "name": ["X", "Y"], "price": [10.0, 20.0]}),
        )
        # bypass the "already exists" assertion on add_data_source by going
        # through the private persistence path.
        dm._data["rep"] = ds2
        dm._persist_datasource(ds2, "rep")

        with dm._engine.connect() as conn:
            rows = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM algomancy_ds__item "
                    'WHERE "_algomancy_dataset_name" = :n'
                ),
                {"n": "rep"},
            ).scalar()
        assert rows == 2  # not 3 — the original single row was deleted

    def test_delete_data_removes_only_its_rows(self, dm):
        """Deleting one dataset must not touch rows owned by another."""
        a = DataSource(ds_type=DataClassification.MASTER_DATA, name="keep_me")
        a.add_table("item", pd.DataFrame({"id": ["k"], "name": ["K"], "price": [1.0]}))
        dm.add_data_source(a)

        b = DataSource(ds_type=DataClassification.MASTER_DATA, name="drop_me")
        b.add_table("item", pd.DataFrame({"id": ["d"], "name": ["D"], "price": [2.0]}))
        dm.add_data_source(b)

        dm.delete_data("drop_me")

        with dm._engine.connect() as conn:
            remaining = conn.execute(
                sa.text('SELECT "_algomancy_dataset_name" FROM algomancy_ds__item')
            ).fetchall()
        names = {row[0] for row in remaining}
        assert names == {"keep_me"}


# ------------------------------------------------------------------ #
# Regression tests for issue #221: dtype coercion on SQL round-trip
# ------------------------------------------------------------------ #


class TypedSchema(Schema):
    """Schema exercising the dtypes that drift across the SQLite round-trip."""

    _FILENAME = "typed"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column(name="id", dtype=DataType.STRING, primary_key=True)
    FLAG = Column(name="flag", dtype=DataType.BOOLEAN)
    COUNT = Column(name="count", dtype=DataType.INTEGER, nullable=True)
    WHEN = Column(name="when", dtype=DataType.DATETIME, nullable=True)


@pytest.fixture
def typed_dm(engine):
    manager = DatabaseDataManager(
        etl_factory=SimpleETLFactory,
        schemas=[TypedSchema()],
        engine=engine,
        session_id="typed",
        data_object_type=DataSource,
    )
    manager.startup()
    return manager


class TestDatabaseDataManagerDtypeRoundTrip:
    """Issue #221 — DataFrames returned by ``get_data`` must match the dtypes
    declared by the registered Schema, even though SQLite normalises them
    across the round-trip."""

    def _reload(self, dm: DatabaseDataManager, name: str) -> pd.DataFrame:
        dm._data.clear()
        ds = dm.get_data(name)
        assert ds is not None
        return ds.tables["typed"]

    def test_boolean_column_survives_roundtrip(self, typed_dm):
        ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="bools")
        ds.add_table(
            "typed",
            pd.DataFrame(
                {
                    "id": ["a", "b"],
                    "flag": [True, False],
                    "count": [1, 2],
                    "when": pd.to_datetime(["2026-01-01", "2026-01-02"]),
                }
            ),
        )
        typed_dm.add_data_source(ds)

        df = self._reload(typed_dm, "bools")
        assert str(df["flag"].dtype) == "boolean", (
            f"BOOLEAN must round-trip as nullable boolean, got {df['flag'].dtype}"
        )
        assert df["flag"].tolist() == [True, False]

    def test_integer_with_nan_survives_roundtrip(self, typed_dm):
        ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="ints")
        ds.add_table(
            "typed",
            pd.DataFrame(
                {
                    "id": ["a", "b", "c"],
                    "flag": [True, False, True],
                    # pandas stores this as float64 because of the None
                    "count": [1, None, 3],
                    "when": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
                }
            ),
        )
        typed_dm.add_data_source(ds)

        df = self._reload(typed_dm, "ints")
        assert str(df["count"].dtype) == "Int64", (
            f"INTEGER must round-trip as nullable Int64, got {df['count'].dtype}"
        )
        assert df["count"].iloc[0] == 1
        assert pd.isna(df["count"].iloc[1])
        assert df["count"].iloc[2] == 3

    def test_datetime_survives_roundtrip(self, typed_dm):
        ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="times")
        ds.add_table(
            "typed",
            pd.DataFrame(
                {
                    "id": ["a"],
                    "flag": [True],
                    "count": [1],
                    "when": pd.to_datetime(["2026-06-10 12:34:56"]),
                }
            ),
        )
        typed_dm.add_data_source(ds)

        df = self._reload(typed_dm, "times")
        assert str(df["when"].dtype) == "datetime64[ns]", (
            f"DATETIME must round-trip as datetime64[ns], got {df['when'].dtype}"
        )
        assert df["when"].iloc[0] == pd.Timestamp("2026-06-10 12:34:56")

    def test_unknown_subtable_skipped_silently(self, engine):
        """A sub-table with no matching Schema must load without coercion or
        raising — preserves behaviour for ad-hoc / test DataSources."""
        dm = DatabaseDataManager(
            etl_factory=SimpleETLFactory,
            schemas=[ItemSchema()],  # only knows "item"
            engine=engine,
            session_id="unknown",
            data_object_type=DataSource,
        )
        dm.startup()
        ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="ad_hoc")
        ds.add_table(
            "ad_hoc_table",  # not declared in any schema
            pd.DataFrame({"x": [1, 2, 3]}),
        )
        dm.add_data_source(ds)

        dm._data.clear()
        reloaded = dm.get_data("ad_hoc")
        assert reloaded is not None
        assert "ad_hoc_table" in reloaded.tables
        # No coercion applied — pandas-inferred dtype passes through.
        assert reloaded.tables["ad_hoc_table"]["x"].tolist() == [1, 2, 3]
