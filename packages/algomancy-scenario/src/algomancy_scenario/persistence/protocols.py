"""Optional protocols for ScenarioResult subclasses to interact with the database backend."""

from typing import Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class SqlResultLayout(Protocol):
    """Opt-in protocol for :class:`BaseScenarioResult` subclasses that want
    per-table SQL storage in :class:`SqlScenarioRepository`.

    Subclasses that don't implement this protocol fall back to JSON-blob
    persistence via the abstract ``to_json`` / ``from_json`` API declared on
    :class:`BaseScenarioResult`. The shape mirrors
    :class:`algomancy_data.database.protocols.SqlTableLayout` exactly but is a
    distinct symbol so the two packages stay decoupled.
    """

    def to_sql_tables(self) -> dict[str, pd.DataFrame]: ...

    def from_sql_tables(self, tables: dict[str, pd.DataFrame]) -> None: ...
