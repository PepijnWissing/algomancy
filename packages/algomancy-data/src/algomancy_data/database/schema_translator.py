"""Translates algomancy-data Column / Schema definitions to SQLAlchemy constructs.

The translation is intentionally one-way (Schema → SQL) and focuses on the
metadata that maps cleanly to SQL constraints. Foreign-key cross-table
references are skipped because dataset table names are constructed dynamically
at runtime and are not suitable for declarative FK constraints.
"""

from typing import List, Type

import sqlalchemy as sa

from ..schema import Column, DataType, Schema


_DTYPE_TO_SA: dict[DataType, type] = {
    DataType.STRING: sa.String,
    DataType.DATETIME: sa.DateTime,
    DataType.INTEGER: sa.BigInteger,
    DataType.FLOAT: sa.Float,
    DataType.BOOLEAN: sa.Boolean,
    DataType.CATEGORICAL: sa.String,
    DataType.INTERVAL: sa.String,
}


def dtype_to_sa_type(dtype: DataType) -> sa.types.TypeEngine:
    """Return a SQLAlchemy type instance for *dtype*."""
    sa_cls = _DTYPE_TO_SA.get(dtype, sa.String)
    return sa_cls()


def column_to_sa(col: Column) -> sa.Column:
    """Convert a single algomancy ``Column`` to a ``sqlalchemy.Column``."""
    sa_type = dtype_to_sa_type(col.dtype)
    kwargs: dict = {
        "nullable": col.nullable or col.optional,
    }
    if col.primary_key:
        kwargs["primary_key"] = True
    if col.unique and not col.primary_key:
        kwargs["unique"] = True
    return sa.Column(col.name, sa_type, **kwargs)


def schema_to_sa_columns(schema: Type[Schema]) -> List[sa.Column]:
    """Return a list of ``sqlalchemy.Column`` objects for a SINGLE-type schema."""
    return [column_to_sa(col) for col in schema.columns()]
