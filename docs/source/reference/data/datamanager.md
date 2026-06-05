(data-manager-ref)=
# DataManager

The DataManager class is responsible for data ingestion and internal storage. 
It is usually not accessed directly, but rather through the ScenarioManager facade. 
Three concrete implementations are available:

- `StatelessDataManager` — in-memory only; no persistence.
- `StatefulDataManager` — persists DataSources to disk as JSON files and reloads them on startup. **Deprecated** — use `DatabaseDataManager` for new projects.
- `DatabaseDataManager` — persists DataSources to a SQL database (requires the `[database]` extra).

## StatelessDataManager / StatefulDataManager

```{deprecated}
`StatefulDataManager` is deprecated and will be removed in a future release.
For persistent storage use {ref}`DatabaseDataManager <database-data-manager-ref>`;
for in-memory-only usage use `StatelessDataManager`.
```

```{eval-rst}
.. automodule:: algomancy_data.datamanager
   :members:
   :undoc-members:
   :show-inheritance:
   :member-order: bysource
```

## DatabaseDataManager

(database-data-manager-ref)=

`DatabaseDataManager` stores DataSources in a SQL database (SQLite by default;
Postgres-compatible). Writes happen immediately after every ETL run, derive, or
`add_data_source` call. `get_data()` loads a DataSource into RAM on first
access and caches it, so only accessed datasets occupy memory.

**Persistence path selection** is dispatched automatically per DataSource:

- *Per-sub-table SQL* (used when the subclass implements {ref}`SqlTableLayout <sql-table-layout-ref>`) —
  each DataFrame becomes a dedicated SQL table (`ds__<session>__<name>__<sub>`),
  externally queryable.
- *JSON-blob fallback* (used for all other `BaseDataSource` subclasses) — the
  DataSource is serialised via its abstract `to_json()` into a `payload` column
  on the `algomancy_datasets` catalogue table.

The bundled `DataSource` satisfies `SqlTableLayout` via its `tables` dict, so
it is always stored as real SQL tables.

**Schema drift** — if an older database is missing the `payload` column,
`startup()` raises immediately with a clear message directing you to drop the
catalogue table and rebuild (there is no automatic migration).

Requires `sqlalchemy>=2.0`. Install via:

```bash
pip install algomancy-data[database]
```

```{eval-rst}
.. automodule:: algomancy_data.database.database_manager
   :members:
   :undoc-members:
   :show-inheritance:
   :member-order: bysource
```
