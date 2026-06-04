"""Optional protocols for DataSource subclasses to interact with the database backend."""

from typing import Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class SqlTableLayout(Protocol):
    """Opt-in protocol for ``BaseDataSource`` subclasses that want per-table SQL
    storage in :class:`DatabaseDataManager`.

    Subclasses that don't implement this protocol fall back to JSON-blob
    persistence via the abstract ``to_json`` / ``from_json`` API declared on
    :class:`BaseDataSource`. The bundled :class:`DataSource` satisfies this
    protocol via its ``tables`` dict, so its DataFrames continue to be written
    as real SQL tables (and remain externally queryable).
    """

    def sql_tables(self) -> dict[str, pd.DataFrame]: ...

    def apply_sql_tables(self, tables: dict[str, pd.DataFrame]) -> None: ...
