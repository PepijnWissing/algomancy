"""Database-backed DataManager implementation.

Uses a SQLAlchemy engine (SQLite by default, Postgres-compatible) to persist
DataSources and their metadata. Two persistence paths are supported and
dispatched on whether the DataSource subclass implements
:class:`SqlTableLayout`:

* **Shared per-sub-table SQL** (default for the bundled :class:`DataSource`) —
  for each sub-table *name* there is exactly one physical SQL table shared by
  all sessions and datasets (e.g. ``algomancy_ds__customers``). Each row carries
  ``_algomancy_session_id`` and ``_algomancy_dataset_name`` discriminator
  columns, so the number of physical tables stays bounded by the project's
  DataSource shape rather than growing with sessions × datasets.
* **JSON blob** (fallback) — the DataSource is serialised via its abstract
  ``to_json`` method into a ``payload`` column on the catalogue. Works for any
  ``BaseDataSource`` subclass, regardless of how it represents its state.
"""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, TYPE_CHECKING

import pandas as pd
import sqlalchemy as sa
from algomancy_utils import Logger

from ..datamanager import DataManager
from ..datasource import DataClassification, BASEDATASOURCE
from ..etl import ETLResult
from ..schema import Schema
from .models import (
    DATA_TABLE_PREFIX,
    DATASET_COL,
    SESSION_COL,
    datasets_table,
    metadata as _catalogue_metadata,
)
from .protocols import SqlTableLayout

if TYPE_CHECKING:
    pass


def _safe_segment(s: str) -> str:
    """Collapse anything that is not alphanumeric or underscore into ``_``."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", s)


def _data_table_name(sub_table: str) -> str:
    """Shared physical table name for a given DataSource sub-table name."""
    return f"{DATA_TABLE_PREFIX}{_safe_segment(sub_table)}"


class DatabaseDataManager(DataManager):
    """DataManager that persists DataSources to a SQL database.

    Writes happen on every ETL / derive / add-from-JSON. ``get_data()``
    materialises a DataSource into RAM on first access and caches it; only
    accessed datasets occupy memory.

    All sessions and datasets share the same set of physical SQL tables — one
    per DataSource sub-table name — so the table count is bounded by the
    project's DataSource shape, not by ``sessions × datasets``. Session and
    dataset are recorded as discriminator columns on every row.

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
        # Catalogue: dataset_name → metadata dict (id, ds_type, creation_datetime, payload, sub_tables)
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
                "sub_tables": _decode_sub_tables(row.sub_tables),
            }
        self.log(
            f"DatabaseDataManager startup for session '{self._session_id}': "
            f"found {len(self._db_catalogue)} datasets."
        )

    def _assert_catalogue_schema_current(self) -> None:
        """Fail fast if the catalogue table predates a required column.

        ``create_all(checkfirst=True)`` does not alter existing tables, so a DB
        that was created before a column was introduced will silently miss the
        column and persist writes will fail in confusing ways. Surface a clear
        error and direct the user at the manual-rebuild path.
        """
        inspector = sa.inspect(self._engine)
        existing = {col["name"] for col in inspector.get_columns("algomancy_datasets")}
        missing = {"payload", "sub_tables"} - existing
        if missing:
            raise RuntimeError(
                f"algomancy_datasets is missing column(s) {sorted(missing)}. "
                "This database was created by an older algomancy-data version. "
                "Drop the algomancy_datasets table (and any algomancy_ds__... "
                "data tables) and rebuild — there is no automatic migration."
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
        info = self._db_catalogue.get(data_key, {})
        sub_tables: List[str] = info.get("sub_tables") or []
        existing_tables = set(sa.inspect(self._engine).get_table_names())
        with self._engine.begin() as conn:
            self._delete_dataset_rows(conn, data_key, sub_tables, existing_tables)
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

    def _delete_dataset_rows(
        self,
        conn: sa.Connection,
        dataset_name: str,
        sub_tables: List[str],
        existing_tables: Optional[set[str]] = None,
    ) -> None:
        """Remove every row this (session, dataset) wrote to the shared tables.

        ``existing_tables`` should be pre-computed OUTSIDE the surrounding
        transaction when this is called inside ``engine.begin()``. Calling
        ``sa.inspect`` inside the transaction borrows a connection and ROLLBACKs
        on release with SingletonThreadPool sqlite (default for
        ``sqlite:///:memory:``), undoing the pending DML.
        """
        if existing_tables is None:
            existing_tables = set(sa.inspect(self._engine).get_table_names())
        for sub in sub_tables:
            table_name = _data_table_name(sub)
            if table_name not in existing_tables:
                continue
            conn.execute(
                sa.text(
                    f'DELETE FROM "{table_name}" '
                    f'WHERE "{SESSION_COL}" = :sid AND "{DATASET_COL}" = :name'
                ),
                {"sid": self._session_id, "name": dataset_name},
            )

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

        # Shared per-sub-table SQL path: requires SqlTableLayout on the subclass.
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

        sub_tables: List[str] = info.get("sub_tables") or []
        inspector = sa.inspect(self._engine)
        existing = set(inspector.get_table_names())
        tables: Dict[str, pd.DataFrame] = {}
        for sub in sub_tables:
            table_name = _data_table_name(sub)
            if table_name not in existing:
                continue
            with self._engine.connect() as conn:
                df = pd.read_sql(
                    sa.text(
                        f'SELECT * FROM "{table_name}" '
                        f'WHERE "{SESSION_COL}" = :sid AND "{DATASET_COL}" = :name'
                    ),
                    conn,
                    params={"sid": self._session_id, "name": dataset_name},
                )
            df = df.drop(columns=[SESSION_COL, DATASET_COL], errors="ignore")
            tables[sub] = df
        ds.from_sql_tables(tables)
        self.log(
            f"Loaded DataSource '{dataset_name}' from database "
            f"({len(tables)} sub-tables)."
        )
        return ds

    def _persist_datasource(
        self, data_source: BASEDATASOURCE, dataset_name: str
    ) -> None:
        payload: Optional[str] = None
        sub_table_names: List[str] = []

        if isinstance(data_source, SqlTableLayout):
            sql_tables = data_source.to_sql_tables()
            sub_table_names = list(sql_tables.keys())
            # Clean up any rows this (session, dataset) wrote previously —
            # including sub-tables that no longer appear in the current shape.
            previous = self._db_catalogue.get(dataset_name, {}).get("sub_tables") or []
            stale = set(previous) - set(sub_table_names)
            existing_tables = set(sa.inspect(self._engine).get_table_names())
            with self._engine.begin() as conn:
                self._delete_dataset_rows(
                    conn,
                    dataset_name,
                    list(stale) + sub_table_names,
                    existing_tables,
                )
                for sub_table, df in sql_tables.items():
                    self._append_to_shared_table(conn, sub_table, dataset_name, df)
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

        sub_tables_json = json.dumps(sub_table_names) if payload is None else None

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
                    sub_tables=sub_tables_json,
                )
            )

        self._db_catalogue[dataset_name] = {
            "id": data_source.id,
            "name": dataset_name,
            "session_id": self._session_id,
            "ds_type": str(data_source._ds_type),
            "creation_datetime": data_source.creation_datetime,
            "payload": payload,
            "sub_tables": sub_table_names if payload is None else None,
        }
        if payload is None:
            self.log(
                f"Persisted DataSource '{dataset_name}' to database "
                f"({len(sub_table_names)} sub-tables)."
            )
        else:
            self.log(
                f"Persisted DataSource '{dataset_name}' to database (JSON payload, "
                f"{len(payload)} chars)."
            )

    def _append_to_shared_table(
        self,
        conn: sa.Connection,
        sub_table: str,
        dataset_name: str,
        df: pd.DataFrame,
    ) -> None:
        """Append ``df`` to the shared physical table for ``sub_table``.

        Prepends the (session_id, dataset_name) discriminator columns. The
        physical table is created on first write with column types inferred
        by pandas — subsequent writes share that schema.
        """
        if SESSION_COL in df.columns or DATASET_COL in df.columns:
            raise ValueError(
                f"DataFrame for sub-table '{sub_table}' must not contain reserved "
                f"columns {SESSION_COL!r} / {DATASET_COL!r}."
            )
        out = df.copy()
        out.insert(0, DATASET_COL, dataset_name)
        out.insert(0, SESSION_COL, self._session_id)
        out.to_sql(
            _data_table_name(sub_table),
            conn,
            if_exists="append",
            index=False,
        )


def _decode_sub_tables(raw: Optional[str]) -> Optional[List[str]]:
    if raw is None:
        return None
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return None
    if isinstance(value, list):
        return [str(v) for v in value]
    return None
