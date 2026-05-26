"""Tests for transformer classes."""

from __future__ import annotations

import pandas as pd

from algomancy_data import Column, DataType, FileExtension, OptionalColumnGuard, Schema
from algomancy_data.schema import SchemaType


class ProductSchema(Schema):
    _FILENAME = "product"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column(name="id", dtype=DataType.STRING, primary_key=True)
    NAME = Column(name="name", dtype=DataType.STRING)
    PRICE = Column(name="price", dtype=DataType.FLOAT, optional=True, default=0.0)


class TestOptionalColumnGuard:
    def test_injects_optional_with_default(self):
        data = {"product": pd.DataFrame({"id": ["a"], "name": ["A"]})}
        OptionalColumnGuard([ProductSchema]).transform(data)
        assert "price" in data["product"].columns
        assert data["product"]["price"].tolist() == [0.0]

    def test_present_optional_untouched(self):
        data = {"product": pd.DataFrame({"id": ["a"], "name": ["A"], "price": [9.5]})}
        OptionalColumnGuard([ProductSchema]).transform(data)
        assert data["product"]["price"].tolist() == [9.5]

    def test_dtype_coercion(self):
        data = {"product": pd.DataFrame({"id": ["a", "b"], "name": ["A", "B"]})}
        OptionalColumnGuard([ProductSchema]).transform(data)
        assert data["product"]["price"].dtype == DataType.FLOAT

    def test_missing_table_is_skipped(self):
        data = {}
        OptionalColumnGuard([ProductSchema]).transform(data)
        assert "product" not in data
