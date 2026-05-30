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
