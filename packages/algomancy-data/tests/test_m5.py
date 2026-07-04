"""Tests for M5 flexibility and extension points."""

from __future__ import annotations

from enum import StrEnum

import pandas as pd
import pytest

from algomancy_data import (
    Column,
    DataFrameExtractor,
    DataType,
    FileExtension,
    ForeignKeyValidator,
    Schema,
    SchemaValidator,
    SimpleETLFactory,
    SingleExtractor,
    get_extractor_class,
    register_extractor,
    registered_keys,
)
from algomancy_data.schema import SchemaType


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #


class OrderSchema(Schema):
    _FILENAME = "order"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ORDER_ID = Column(name="order_id", dtype=DataType.STRING, primary_key=True)
    PRODUCT_ID = Column(name="product_id", dtype=DataType.STRING)


class ProductSchema(Schema):
    _FILENAME = "product"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column(name="id", dtype=DataType.STRING, primary_key=True)
    NAME = Column(name="name", dtype=DataType.STRING)


# ------------------------------------------------------------------ #
# Issue #97 — public register_extractor API
# ------------------------------------------------------------------ #


class _FakeExt(StrEnum):
    FOO = "foo"


class _FakeExtractor(SingleExtractor):
    def _extract_file(self):
        return pd.DataFrame({"id": ["x"]})


class TestPublicRegisterExtractor:
    def test_register_and_lookup(self):
        register_extractor(_FakeExt.FOO, SchemaType.SINGLE, _FakeExtractor)
        try:
            assert (
                get_extractor_class(_FakeExt.FOO, SchemaType.SINGLE) is _FakeExtractor
            )
            assert (_FakeExt.FOO, SchemaType.SINGLE) in registered_keys()
        finally:
            # No public unregister API; overwrite with a sentinel to keep tests
            # idempotent. Subsequent test runs will overwrite again.
            pass

    def test_end_to_end_registration(self):
        """A user-defined extractor wired through the registry runs."""

        class _IdSchema(Schema):
            _FILENAME = "ids"
            _EXTENSION = _FakeExt.FOO
            _SCHEMA_TYPE = SchemaType.SINGLE

            ID = Column(name="id", dtype=DataType.STRING)

        register_extractor(_FakeExt.FOO, SchemaType.SINGLE, _FakeExtractor)

        # We do not run the full pipeline here; just confirm the factory
        # produces an extractor of the registered class for the schema.
        class _Fake:
            def __init__(self):
                self.name = "ids"
                self.path = None
                self.content = "id\nx\n"

        seq = SimpleETLFactory.create_extraction_sequence(
            {"ids": _Fake()}, {"ids": _IdSchema}
        )
        assert isinstance(seq._extractors[0], _FakeExtractor)


# ------------------------------------------------------------------ #
# Issue #98 — ForeignKeyValidator
# ------------------------------------------------------------------ #


class TestForeignKeyValidator:
    def test_all_valid(self):
        data = {
            "product": pd.DataFrame({"id": ["p1", "p2"], "name": ["A", "B"]}),
            "order": pd.DataFrame(
                {"order_id": ["o1", "o2"], "product_id": ["p1", "p2"]}
            ),
        }
        v = ForeignKeyValidator("order", "product_id", "product", "id")
        assert v.validate(data) == []

    def test_violation_reported(self):
        data = {
            "product": pd.DataFrame({"id": ["p1"], "name": ["A"]}),
            "order": pd.DataFrame(
                {"order_id": ["o1", "o2"], "product_id": ["p1", "p99"]}
            ),
        }
        v = ForeignKeyValidator("order", "product_id", "product", "id")
        msgs = v.validate(data)
        assert len(msgs) == 1
        assert msgs[0].code == "FK_VIOLATION"
        assert msgs[0].table == "order"
        assert msgs[0].row == 1

    def test_composite_key(self):
        data = {
            "right": pd.DataFrame({"a": ["x", "y"], "b": [1, 2]}),
            "left": pd.DataFrame({"a": ["x", "z"], "b": [1, 2]}),
        }
        v = ForeignKeyValidator("left", ["a", "b"], "right", ["a", "b"])
        msgs = v.validate(data)
        assert len(msgs) == 1
        assert msgs[0].column == "a,b"

    def test_missing_table(self):
        v = ForeignKeyValidator("a", "x", "b", "y")
        msgs = v.validate({"a": pd.DataFrame({"x": [1]})})
        assert any(m.code == "TABLE_NOT_FOUND" for m in msgs)

    def test_left_col_missing(self):
        v = ForeignKeyValidator("a", "nope", "b", "y")
        msgs = v.validate(
            {"a": pd.DataFrame({"x": [1]}), "b": pd.DataFrame({"y": [1]})}
        )
        assert msgs[0].code == "COLUMN_NOT_FOUND"

    def test_unequal_length_raises(self):
        with pytest.raises(ValueError, match="same length"):
            ForeignKeyValidator("a", ["x", "y"], "b", "z")

    def test_from_schemas_derives_validator(self):
        """#116 — `ForeignKeyValidator.from_schemas` builds validators from
        `Column.foreign_key` declarations on the supplied schemas."""
        from algomancy_data import Column, DataType, FileExtension, Schema
        from algomancy_data.schema import SchemaType

        class _Product(Schema):
            _FILENAME = "product"
            _EXTENSION = FileExtension.CSV
            _SCHEMA_TYPE = SchemaType.SINGLE
            ID = Column(name="id", dtype=DataType.STRING, primary_key=True)

        class _Order(Schema):
            _FILENAME = "order"
            _EXTENSION = FileExtension.CSV
            _SCHEMA_TYPE = SchemaType.SINGLE
            ID = Column(name="id", dtype=DataType.STRING, primary_key=True)
            PRODUCT_ID = Column(
                name="product_id",
                dtype=DataType.STRING,
                foreign_key=("product", "id"),
            )

        validators = ForeignKeyValidator.from_schemas([_Order, _Product])
        assert len(validators) == 1
        v = validators[0]
        assert v.left_table == "order"
        assert v.left_col == ["product_id"]
        assert v.right_table == "product"
        assert v.right_col == ["id"]

    def test_from_schemas_matches_explicit_on_violation(self):
        from algomancy_data import Column, DataType, FileExtension, Schema
        from algomancy_data.schema import SchemaType

        class _Product(Schema):
            _FILENAME = "product"
            _EXTENSION = FileExtension.CSV
            _SCHEMA_TYPE = SchemaType.SINGLE
            ID = Column(name="id", dtype=DataType.STRING, primary_key=True)

        class _Order(Schema):
            _FILENAME = "order"
            _EXTENSION = FileExtension.CSV
            _SCHEMA_TYPE = SchemaType.SINGLE
            ID = Column(name="id", dtype=DataType.STRING, primary_key=True)
            PRODUCT_ID = Column(
                name="product_id",
                dtype=DataType.STRING,
                foreign_key=("product", "id"),
            )

        data = {
            "product": pd.DataFrame({"id": ["p1"]}),
            "order": pd.DataFrame({"id": ["o1", "o2"], "product_id": ["p1", "BAD"]}),
        }
        derived = ForeignKeyValidator.from_schemas([_Order, _Product])[0]
        explicit = ForeignKeyValidator("order", "product_id", "product", "id")
        d_msgs = derived.validate(data)
        e_msgs = explicit.validate(data)
        assert len(d_msgs) == len(e_msgs) == 1
        assert d_msgs[0].code == e_msgs[0].code == "FK_VIOLATION"
        assert d_msgs[0].row == e_msgs[0].row

    def test_from_schemas_no_fk_returns_empty(self):
        from algomancy_data import Column, DataType, FileExtension, Schema
        from algomancy_data.schema import SchemaType

        class _Product(Schema):
            _FILENAME = "product"
            _EXTENSION = FileExtension.CSV
            _SCHEMA_TYPE = SchemaType.SINGLE
            ID = Column(name="id", dtype=DataType.STRING, primary_key=True)

        assert ForeignKeyValidator.from_schemas([_Product]) == []


# ------------------------------------------------------------------ #
# Issue #99 — DataFrameExtractor
# ------------------------------------------------------------------ #


class TestDataFrameExtractor:
    def test_returns_dataframe(self):
        df = pd.DataFrame({"id": ["p1"], "name": ["A"]})
        ex = DataFrameExtractor("product", df, ProductSchema)
        out = ex.extract()
        assert "product" in out
        assert out["product"]["name"].tolist() == ["A"]

    def test_dtype_coercion_via_schema(self):
        # Schema says id should be STRING; pass int and see it coerced.
        class IntIdSchema(Schema):
            _FILENAME = "x"
            _EXTENSION = FileExtension.CSV
            _SCHEMA_TYPE = SchemaType.SINGLE

            ID = Column(name="id", dtype=DataType.STRING)

        df = pd.DataFrame({"id": [1, 2, 3]})
        out = DataFrameExtractor("x", df, IntIdSchema).extract()
        assert out["x"]["id"].dtype == DataType.STRING

    def test_multi_schema_rejected(self):
        class MultiS(Schema):
            _FILENAME = "m"
            _EXTENSION = FileExtension.XLSX
            _SCHEMA_TYPE = SchemaType.MULTI
            _DATATYPES = {"A": {"a": DataType.STRING}}

        with pytest.raises(ValueError, match="SINGLE schemas"):
            DataFrameExtractor("m", pd.DataFrame(), MultiS)

    def test_does_not_mutate_input(self):
        df = pd.DataFrame({"id": [1]})
        original = df.copy()
        DataFrameExtractor("product", df, ProductSchema).extract()
        pd.testing.assert_frame_equal(df, original)


# ------------------------------------------------------------------ #
# Default validation sequence still works with custom validators
# ------------------------------------------------------------------ #


class TestCustomFactoryFK:
    def test_simple_factory_plus_fk_check(self):
        class _FKFactory(SimpleETLFactory):
            @classmethod
            def create_validation_sequence(cls, schemas, logger=None):
                seq = super().create_validation_sequence(schemas, logger)
                seq.add_validator(
                    ForeignKeyValidator("order", "product_id", "product", "id")
                )
                return seq

        schemas = {s.file_name(): s for s in (OrderSchema, ProductSchema)}
        seq = _FKFactory.create_validation_sequence(schemas)
        assert any(isinstance(v, ForeignKeyValidator) for v in seq._validators)
        assert any(isinstance(v, SchemaValidator) for v in seq._validators)
