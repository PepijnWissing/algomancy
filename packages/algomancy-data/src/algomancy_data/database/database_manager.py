"""Database-backed DataManager implementation.

Uses a SQLAlchemy engine (SQLite by default, Postgres-compatible) to persist
DataSources and their metadata. Two persistence paths are supported and
dispatched on whether the DataSource subclass implements
:class:`SqlTableLayout`:

* **Per-sub-table SQL** (default for the bundled :class:`DataSource`) — each
  DataFrame is written via ``DataFrame.to_sql`` to a dedicated table. Data is
  externally queryable and DataSources are materialised into RAM lazily on
  ``get_data()``.
* **JSON blob** (fallback) — the DataSource is serialised via its abstract
  ``to_json`` method into a ``payload`` column on the catalogue. Works for any
  ``BaseDataSource`` subclass, regardless of how it represents its state.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, TYPE_CHECKING

import pandas as pd
import sqlalchemy as sa
from algomancy_utils import Logger

from ..datamanager import DataManager
from ..datasource import DataClassification, BASEDATASOURCE
from ..etl import ETLResult
from ..schema import Schema
from .models import metadata as _catalogue_metadata, datasets_table
from .protocols import SqlTableLayout

if TYPE_CHECKING:
    pass


def _safe_segment(s: str) -> str:
    """Collapse anything that is not alphanumeric or underscore into ``_``."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", s)


def _data_table_name(session_id: str, dataset_name: str, sub_table: str) -> str:
    """Deterministic SQL table name for one sub-table of a DataSource."""
    return f"ds__{_safe_segment(session_id)}__{_safe_segment(dataset_name)}__{_safe_segment(sub_table)}"


def _data_table_prefix(session_id: str, dataset_name: str) -> str:
    return f"ds__{_safe_segment(session_id)}__{_safe_segment(dataset_name)}__"


class DatabaseDataManager(DataManager):
    """DataManager that persists DataSources to a SQL database.

    Writes happen on every ETL / derive / add-from-JSON. ``get_data()``
    materialises a DataSource into RAM on first access and caches it; only
    accessed datasets occupy memory.

    The class works for any :class:`BaseDataSource` subclass: subclasses that
    implement :class:`SqlTableLayout` get per-sub-table SQL storage, others
    fall back to a JSON-blob payload on the catalogue.

    Args:
        etl_factory: ETL factory class (same as for other DataManager variants).
        schemas: List of Schema instances.
        engine: A SQLAlchemy ``Engine`` pointed at the target database.
        session_id: Logical name of the session that owns this manager instance.
        data_object_type: ``BaseDataSource`` subclass to instantiate when
            loading DataSources from the DB. Must implement ``from_json`` when
            the JSON-blob fallback path is in use.
        logger: Optional logger.
    """

    def __init__(
        self,
        etl_factory: type,
        schemas: List[Schema],
        engine: sa.Engine,
        session_id: str,
        data_object_type: type[BASEDATASOURCE],
        logger: Logger | None = None,
    ) -> None:
        super().__init__(etl_factory, schemas, "database", data_object_type, logger)
        self._engine = engine
        self._session_id = session_id
        # Catalogue: dataset_name → metadata dict (id, ds_type, creation_datetime, payload)
        self._db_catalogue: Dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def startup(self) -> None:
        """Initialise DB schema and load dataset metadata (not data)."""
        _catalogue_metadata.create_all(self._engine, checkfirst=True)
        self._assert_catalogue_schema_current()
        with self._engine.connect() as conn:
            rows = conn.execute(
                datasets_table.select().where(
                    datasets_table.c.session_id == self._session_id
                )
            ).fetchall()
        for row in rows:
            self._db_catalogue[row.name] = {
                "id": row.id,
                "name": row.name,
                "session_id": row.session_id,
                "ds_type": row.ds_type,
                "creation_datetime": row.creation_datetime,
                "payload": row.payload,
            }
        self.log(
            f"DatabaseDataManager startup for session '{self._session_id}': "
            f"found {len(self._db_catalogue)} datasets."
        )

    def _assert_catalogue_schema_current(self) -> None:
        """Fail fast if the catalogue table predates a required column.

        ``create_all(checkfirst=True)`` does not alter existing tables, so a DB
        that was created before ``payload`` was introduced will silently miss
        the column and persist writes will fail in confusing ways. Surface a
        clear error and direct the user at the manual-rebuild path.
        """
        inspector = sa.inspect(self._engine)
        existing = {col["name"] for col in inspector.get_columns("algomancy_datasets")}
        missing = {"payload"} - existing
        if missing:
            raise RuntimeError(
                f"algomancy_datasets is missing column(s) {sorted(missing)}. "
                "This database was created by an older algomancy-data version. "
                "Drop the algomancy_datasets table (and any ds__... data tables) "
                "and rebuild — there is no automatic migration."
            )

    # ------------------------------------------------------------------
    # Accessors (override to include DB catalogue)
    # ------------------------------------------------------------------

    def get_data_keys(self) -> List[str]:
        known = set(self._db_catalogue.keys()) | set(self._data.keys())
        return list(known)

    def get_data(self, data_key: str) -> Optional[BASEDATASOURCE]:
        if data_key in self._data:
            return self._data[data_key]
        if data_key in self._db_catalogue:
            ds = self._load_datasource_from_db(data_key)
            if ds is not None:
                self._data[data_key] = ds
            return ds
        return None

    # ------------------------------------------------------------------
    # Write operations (override to persist to DB)
    # ------------------------------------------------------------------

    def etl_data(self, files, dataset_name: str) -> ETLResult:
        result = super().etl_data(files, dataset_name)
        if result.is_success:
            self._persist_datasource(result.datasource, dataset_name)
        return result

    def add_data_source(self, data_source: BASEDATASOURCE) -> None:
        super().add_data_source(data_source)
        self._persist_datasource(data_source, str(data_source.name))

    def derive_data(self, existing_key: str, derived_key: str) -> None:
        assert existing_key in self.get_data_keys(), f"Data '{existing_key}' not found."
        assert derived_key not in self.get_data_keys(), (
            f"Data '{derived_key}' already exists."
        )
        existing = self.get_data(existing_key)
        derived = existing.derive(derived_key)
        self._data[derived_key] = derived
        self._persist_datasource(derived, derived_key)
        self.log(f"Derived data '{derived_key}' derived from '{existing_key}'.")

    def delete_data(
        self, data_key: str, prevent_masterdata_removal: bool = False
    ) -> None:
        assert data_key in self.get_data_keys(), f"Data '{data_key}' not found."
        inspector = sa.inspect(self._engine)
        prefix = _data_table_prefix(self._session_id, data_key)
        with self._engine.begin() as conn:
            for table_name in inspector.get_table_names():
                if table_name.startswith(prefix):
                    conn.execute(sa.text(f'DROP TABLE IF EXISTS "{table_name}"'))
            conn.execute(
                datasets_table.delete().where(
                    (datasets_table.c.session_id == self._session_id)
                    & (datasets_table.c.name == data_key)
                )
            )
        self._db_catalogue.pop(data_key, None)
        self._data.pop(data_key, None)
        self.log(f"Data '{data_key}' deleted from database.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_datasource_from_db(self, dataset_name: str) -> Optional[BASEDATASOURCE]:
        info = self._db_catalogue.get(dataset_name)
        if not info:
            return None

        payload = info.get("payload")
        if payload is not None:
            # JSON-blob path: universal — works for any subclass with from_json.
            ds = self._data_object_type.from_json(payload)
            self.log(
                f"Loaded DataSource '{dataset_name}' from database (JSON payload)."
            )
            return ds

        # Per-sub-table SQL path: requires SqlTableLayout on the subclass.
        try:
            ds_type = DataClassification(info["ds_type"])
        except ValueError:
            self.log(
                f"Unknown DataClassification '{info['ds_type']}' for '{dataset_name}'. Skipping."
            )
            return None

        ds = self._data_object_type(
            ds_type=ds_type,
            name=dataset_name,
            ds_id=info["id"],
            creation_datetime=info.get("creation_datetime"),
        )
        if not isinstance(ds, SqlTableLayout):
            raise TypeError(
                f"DataSource '{dataset_name}' was persisted as per-table SQL but "
                f"data_object_type {self._data_object_type.__name__} does not "
                "implement SqlTableLayout. Either restore the original "
                "data_object_type or delete and re-persist the dataset."
            )

        prefix = _data_table_prefix(self._session_id, dataset_name)
        tables: Dict[str, pd.DataFrame] = {}
        inspector = sa.inspect(self._engine)
        for table_name in inspector.get_table_names():
            if table_name.startswith(prefix):
                sub_table = table_name[len(prefix) :]
                with self._engine.connect() as conn:
                    tables[sub_table] = pd.read_sql_table(table_name, conn)
        ds.from_sql_tables(tables)
        self.log(
            f"Loaded DataSource '{dataset_name}' from database ({len(tables)} tables)."
        )
        return ds

    def _persist_datasource(
        self, data_source: BASEDATASOURCE, dataset_name: str
    ) -> None:
        payload: Optional[str] = None
        sub_table_count = 0

        if isinstance(data_source, SqlTableLayout):
            for sub_table, df in data_source.to_sql_tables().items():
                sql_name = _data_table_name(self._session_id, dataset_name, sub_table)
                with self._engine.begin() as conn:
                    df.to_sql(sql_name, conn, if_exists="replace", index=False)
                sub_table_count += 1
        else:
            payload = data_source.to_json()

        # Coerce creation_datetime: after a JSON round-trip it may arrive as a string
        from datetime import datetime as _dt

        creation_dt = data_source.creation_datetime
        if isinstance(creation_dt, str):
            try:
                creation_dt = _dt.fromisoformat(creation_dt)
            except ValueError:
                creation_dt = None

        # Upsert catalogue row
        with self._engine.begin() as conn:
            conn.execute(
                datasets_table.delete().where(
                    (datasets_table.c.session_id == self._session_id)
                    & (datasets_table.c.name == dataset_name)
                )
            )
            conn.execute(
                datasets_table.insert().values(
                    id=data_source.id,
                    name=dataset_name,
                    session_id=self._session_id,
                    ds_type=str(data_source._ds_type),
                    creation_datetime=creation_dt,
                    payload=payload,
                )
            )

        self._db_catalogue[dataset_name] = {
            "id": data_source.id,
            "name": dataset_name,
            "session_id": self._session_id,
            "ds_type": str(data_source._ds_type),
            "creation_datetime": data_source.creation_datetime,
            "payload": payload,
        }
        if payload is None:
            self.log(
                f"Persisted DataSource '{dataset_name}' to database "
                f"({sub_table_count} tables)."
            )
        else:
            self.log(
                f"Persisted DataSource '{dataset_name}' to database (JSON payload, "
                f"{len(payload)} chars)."
            )
