"""Translates algomancy-data Column / Schema definitions to SQLAlchemy constructs.

The translation is intentionally one-way (Schema → SQL) and focuses on the
metadata that maps cleanly to SQL constraints. Foreign-key cross-table
references are skipped because dataset table names are constructed dynamically
at runtime and are not suitable for declarative FK constraints.
"""

from typing import List, Type

import pandas as pd
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


# Per-DataType target pandas dtype used by ``coerce_dataframe_to_schema``.
# Nullable dtypes are used wherever a SQL round-trip can reintroduce nulls
# (e.g. INTEGER ↔ float64 once a NaN appears).
_DTYPE_TO_PANDAS: dict[DataType, str] = {
    DataType.STRING: "string",
    DataType.INTEGER: "Int64",
    DataType.FLOAT: "Float64",
    DataType.BOOLEAN: "boolean",
    DataType.CATEGORICAL: "category",
}


def coerce_dataframe_to_schema(df: pd.DataFrame, schema: Type[Schema]) -> pd.DataFrame:
    """Coerce *df* columns to the dtypes declared by *schema*.

    Called after ``pd.read_sql()`` to restore dtypes lost across the SQL
    round-trip. Columns absent from the schema are left untouched. Columns
    declared by the schema but missing from *df* are left missing (a
    downstream Schema/Required-column validator reports that case).

    Failures on individual columns leave that column untouched rather than
    aborting the load — the divergence will surface in the next validator
    run instead of crashing reload.

    MULTI schemas should be reduced to a synthetic SINGLE sub-schema by the
    caller (e.g. via ``Schema.get_subschema(sub_name)``) before being passed
    here.
    """
    if not schema.is_single():
        return df

    out = df
    copied = False
    for col_name, target in schema.datatypes().items():
        if col_name not in out.columns:
            continue
        try:
            if target == DataType.DATETIME:
                new_series = pd.to_datetime(out[col_name], errors="coerce")
            elif target == DataType.INTERVAL:
                # Stored as string; no canonical pandas dtype to coerce to.
                continue
            else:
                pandas_dtype = _DTYPE_TO_PANDAS.get(target)
                if pandas_dtype is None or str(out[col_name].dtype) == pandas_dtype:
                    continue
                new_series = out[col_name].astype(pandas_dtype)
        except TypeError, ValueError:
            continue
        if not copied:
            out = out.copy()
            copied = True
        out[col_name] = new_series
    return out
