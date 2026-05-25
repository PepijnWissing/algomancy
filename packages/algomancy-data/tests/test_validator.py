"""Tests for the structured validation framework (M2)."""

from __future__ import annotations

import pandas as pd
import pytest

from algomancy_data import (
    Column,
    DataType,
    FileExtension,
    MissingValueValidator,
    OptionalColumnGuard,
    PrimaryKeyValidator,
    RequiredColumnsValidator,
    Schema,
    SchemaValidator,
    UniqueValueValidator,
    ValidationMessage,
    ValidationResult,
    ValidationSequence,
    ValidationSeverity,
    Validator,
)
from algomancy_data.schema import SchemaType


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #


class ProductSchema(Schema):
    _FILENAME = "product"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column(name="id", dtype=DataType.STRING, primary_key=True)
    NAME = Column(name="name", dtype=DataType.STRING)
    PRICE = Column(name="price", dtype=DataType.FLOAT, optional=True, default=0.0)


class OrderSchema(Schema):
    _FILENAME = "order"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ORDER_ID = Column(name="order_id", dtype=DataType.STRING, primary_key=True)
    PRODUCT_ID = Column(name="product_id", dtype=DataType.STRING, primary_key=True)
    QTY = Column(name="qty", dtype=DataType.INTEGER)


@pytest.fixture
def good_data():
    return {
        "product": pd.DataFrame(
            {"id": ["a", "b", "c"], "name": ["A", "B", "C"], "price": [1.0, 2.0, 3.0]}
        )
    }


# ------------------------------------------------------------------ #
# Issue #79 — ValidationMessage structured fields
# ------------------------------------------------------------------ #


class TestValidationMessage:
    def test_positional_back_compat(self):
        msg = ValidationMessage(ValidationSeverity.ERROR, "boom")
        assert msg.severity == ValidationSeverity.ERROR
        assert msg.message == "boom"
        assert msg.table is None
        assert msg.column is None
        assert msg.row is None
        assert msg.code is None

    def test_structured_fields(self):
        msg = ValidationMessage(
            ValidationSeverity.WARNING,
            "bad row",
            table="product",
            column="price",
            row=3,
            code="DTYPE_MISMATCH",
        )
        assert msg.table == "product"
        assert msg.column == "price"
        assert msg.row == 3
        assert msg.code == "DTYPE_MISMATCH"

    def test_str_includes_location(self):
        msg = ValidationMessage(
            ValidationSeverity.ERROR, "boom", table="t", column="c", row=1
        )
        s = str(msg)
        assert "ERROR" in s
        assert "boom" in s
        assert "table=t" in s
        assert "column=c" in s
        assert "row=1" in s

    def test_str_plain_when_no_location(self):
        assert str(ValidationMessage(ValidationSeverity.INFO, "ok")) == "INFO: ok"

    def test_clean_escapes_newlines(self):
        msg = ValidationMessage(ValidationSeverity.INFO, "a\nb\tc")
        assert msg.message == "a\\nb\\tc"

    def test_equality(self):
        a = ValidationMessage(ValidationSeverity.ERROR, "x", table="t")
        b = ValidationMessage(ValidationSeverity.ERROR, "x", table="t")
        c = ValidationMessage(ValidationSeverity.ERROR, "x")
        assert a == b
        assert a != c


# ------------------------------------------------------------------ #
# Issue #85 — ValidationResult
# ------------------------------------------------------------------ #


class TestValidationResult:
    def test_is_valid_no_messages(self):
        seq = ValidationSequence()
        result = seq.run_validation({})
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.messages == []

    def test_counts_by_severity(self):
        class FixedValidator(Validator):
            def validate(self, data):
                self.add_message(ValidationSeverity.INFO, "i")
                self.add_message(ValidationSeverity.WARNING, "w")
                self.add_message(ValidationSeverity.ERROR, "e")
                return self.messages

        seq = ValidationSequence([FixedValidator()])
        result = seq.run_validation({})
        assert result.counts_by_severity["INFO"] == 1
        assert result.counts_by_severity["WARNING"] == 1
        assert result.counts_by_severity["ERROR"] == 1

    def test_as_dataframe(self):
        class FixedValidator(Validator):
            def validate(self, data):
                self.add_message(
                    ValidationSeverity.ERROR, "boom", table="t", column="c", row=2
                )
                return self.messages

        seq = ValidationSequence([FixedValidator()])
        result = seq.run_validation({})
        df = result.as_dataframe()
        assert len(df) == 1
        assert df.iloc[0]["table"] == "t"
        assert df.iloc[0]["column"] == "c"
        assert df.iloc[0]["row"] == 2

    def test_as_dataframe_empty(self):
        seq = ValidationSequence()
        df = seq.run_validation({}).as_dataframe()
        assert list(df.columns) == [
            "severity",
            "message",
            "table",
            "column",
            "row",
            "code",
        ]

    def test_messages_by_severity(self):
        result = ValidationResult(
            is_valid=False,
            messages=[
                ValidationMessage(ValidationSeverity.ERROR, "a"),
                ValidationMessage(ValidationSeverity.WARNING, "b"),
            ],
        )
        assert len(result.messages_by_severity(ValidationSeverity.ERROR)) == 1
        assert len(result.messages_at_least(ValidationSeverity.WARNING)) == 2

    def test_bool_and_iter(self):
        result = ValidationResult(is_valid=True)
        assert bool(result) is True
        assert list(iter(result)) == []
        assert len(result) == 0


# ------------------------------------------------------------------ #
# Issue #84 — ValidationSequence.halt_on
# ------------------------------------------------------------------ #


class TestHaltOn:
    class _ErrorValidator(Validator):
        def validate(self, data):
            self.add_message(ValidationSeverity.ERROR, "an error")
            return self.messages

    def test_default_halts_only_on_critical(self):
        seq = ValidationSequence([self._ErrorValidator()])
        result = seq.run_validation({})
        assert result.is_valid is True
        assert result.halt_on == ValidationSeverity.CRITICAL

    def test_halt_on_error_invalidates(self):
        seq = ValidationSequence(
            [self._ErrorValidator()], halt_on=ValidationSeverity.ERROR
        )
        result = seq.run_validation({})
        assert result.is_valid is False

    def test_halt_on_warning_promotes(self):
        class WarnValidator(Validator):
            def validate(self, data):
                self.add_message(ValidationSeverity.WARNING, "w")
                return self.messages

        seq = ValidationSequence([WarnValidator()], halt_on=ValidationSeverity.WARNING)
        result = seq.run_validation({})
        assert result.is_valid is False


# ------------------------------------------------------------------ #
# Issue #80 — RequiredColumnsValidator
# ------------------------------------------------------------------ #


class TestRequiredColumnsValidator:
    def test_all_present(self, good_data):
        v = RequiredColumnsValidator([ProductSchema])
        msgs = v.validate(good_data)
        assert msgs == []

    def test_missing_required(self):
        data = {"product": pd.DataFrame({"id": ["a"], "price": [1.0]})}
        v = RequiredColumnsValidator([ProductSchema])
        msgs = v.validate(data)
        assert len(msgs) == 1
        assert msgs[0].table == "product"
        assert msgs[0].column == "name"
        assert msgs[0].code == "MISSING_REQUIRED_COLUMN"
        assert msgs[0].severity == ValidationSeverity.ERROR

    def test_extra_columns_are_not_flagged(self):
        data = {
            "product": pd.DataFrame(
                {"id": ["a"], "name": ["A"], "extra": [9], "price": [1.0]}
            )
        }
        v = RequiredColumnsValidator([ProductSchema])
        msgs = v.validate(data)
        assert msgs == []

    def test_optional_columns_not_required(self):
        data = {"product": pd.DataFrame({"id": ["a"], "name": ["A"]})}
        v = RequiredColumnsValidator([ProductSchema])
        msgs = v.validate(data)
        assert msgs == []

    def test_configurable_severity(self):
        data = {"product": pd.DataFrame({"id": ["a"]})}
        v = RequiredColumnsValidator(
            [ProductSchema], severity=ValidationSeverity.CRITICAL
        )
        msgs = v.validate(data)
        assert all(m.severity == ValidationSeverity.CRITICAL for m in msgs)


# ------------------------------------------------------------------ #
# Issue #81 — OptionalColumnGuard
# ------------------------------------------------------------------ #


class TestOptionalColumnGuard:
    def test_injects_optional_with_default(self):
        data = {"product": pd.DataFrame({"id": ["a"], "name": ["A"]})}
        v = OptionalColumnGuard([ProductSchema])
        msgs = v.validate(data)
        assert "price" in data["product"].columns
        assert data["product"]["price"].tolist() == [0.0]
        assert any(m.code == "OPTIONAL_COLUMN_INJECTED" for m in msgs)

    def test_present_optional_untouched(self):
        df = pd.DataFrame({"id": ["a"], "name": ["A"], "price": [9.5]})
        data = {"product": df}
        OptionalColumnGuard([ProductSchema]).validate(data)
        assert data["product"]["price"].tolist() == [9.5]

    def test_dtype_coercion(self):
        data = {"product": pd.DataFrame({"id": ["a", "b"], "name": ["A", "B"]})}
        OptionalColumnGuard([ProductSchema]).validate(data)
        assert data["product"]["price"].dtype == DataType.FLOAT


# ------------------------------------------------------------------ #
# Issue #82 — PrimaryKeyValidator
# ------------------------------------------------------------------ #


class TestPrimaryKeyValidator:
    def test_clean_table_passes(self, good_data):
        v = PrimaryKeyValidator([ProductSchema])
        msgs = v.validate(good_data)
        assert msgs == []

    def test_duplicate_single_pk(self):
        data = {
            "product": pd.DataFrame(
                {"id": ["a", "a"], "name": ["A1", "A2"], "price": [1.0, 2.0]}
            )
        }
        v = PrimaryKeyValidator([ProductSchema])
        msgs = v.validate(data)
        codes = {m.code for m in msgs}
        assert "PK_DUPLICATE" in codes
        assert all(m.table == "product" for m in msgs)

    def test_null_in_pk(self):
        data = {
            "product": pd.DataFrame(
                {"id": [None, "b"], "name": ["A", "B"], "price": [1.0, 2.0]}
            )
        }
        v = PrimaryKeyValidator([ProductSchema])
        msgs = v.validate(data)
        codes = {m.code for m in msgs}
        assert "PK_NULL" in codes

    def test_joint_pk(self):
        data = {
            "order": pd.DataFrame(
                {
                    "order_id": ["o1", "o1", "o2"],
                    "product_id": ["p1", "p1", "p2"],
                    "qty": [1, 2, 3],
                }
            )
        }
        v = PrimaryKeyValidator([OrderSchema])
        msgs = v.validate(data)
        dup_rows = [m for m in msgs if m.code == "PK_DUPLICATE"]
        # Two rows form the duplicate pair → two messages
        assert len(dup_rows) == 2

    def test_no_pk_skipped(self):
        class NoPK(Schema):
            _FILENAME = "x"
            _EXTENSION = FileExtension.CSV
            _SCHEMA_TYPE = SchemaType.SINGLE
            A = Column(name="a", dtype=DataType.STRING)

        v = PrimaryKeyValidator([NoPK])
        msgs = v.validate({"x": pd.DataFrame({"a": ["1", "1"]})})
        assert msgs == []


# ------------------------------------------------------------------ #
# Issue #83 — UniqueValueValidator / MissingValueValidator
# ------------------------------------------------------------------ #


class TestUniqueValueValidator:
    def test_no_duplicates(self):
        data = {"t": pd.DataFrame({"x": [1, 2, 3]})}
        v = UniqueValueValidator(table="t", columns=["x"])
        assert v.validate(data) == []

    def test_duplicates_reported(self):
        data = {"t": pd.DataFrame({"x": [1, 1, 2]})}
        v = UniqueValueValidator(table="t", columns=["x"])
        msgs = v.validate(data)
        assert len(msgs) == 2
        assert all(m.code == "DUPLICATE_VALUE" for m in msgs)

    def test_missing_table(self):
        v = UniqueValueValidator(table="missing", columns=["x"])
        msgs = v.validate({})
        assert msgs[0].code == "TABLE_NOT_FOUND"

    def test_missing_column(self):
        v = UniqueValueValidator(table="t", columns=["nope"])
        msgs = v.validate({"t": pd.DataFrame({"x": [1]})})
        assert msgs[0].code == "COLUMN_NOT_FOUND"

    def test_configurable_severity(self):
        v = UniqueValueValidator(
            table="t", columns=["x"], severity=ValidationSeverity.WARNING
        )
        msgs = v.validate({"t": pd.DataFrame({"x": [1, 1]})})
        assert all(m.severity == ValidationSeverity.WARNING for m in msgs)


class TestMissingValueValidator:
    def test_no_nulls(self):
        v = MissingValueValidator(table="t", columns=["x"])
        assert v.validate({"t": pd.DataFrame({"x": [1, 2]})}) == []

    def test_nulls_reported(self):
        v = MissingValueValidator(table="t", columns=["x"])
        msgs = v.validate({"t": pd.DataFrame({"x": [1, None, 3]})})
        assert len(msgs) == 1
        assert msgs[0].row == 1
        assert msgs[0].code == "NULL_VALUE"

    def test_multiple_columns(self):
        v = MissingValueValidator(table="t", columns=["x", "y"])
        msgs = v.validate({"t": pd.DataFrame({"x": [1, None], "y": [None, 2]})})
        codes = [m.code for m in msgs]
        cols = [m.column for m in msgs]
        assert codes.count("NULL_VALUE") == 2
        assert set(cols) == {"x", "y"}


# ------------------------------------------------------------------ #
# Existing SchemaValidator — structured fields preserved
# ------------------------------------------------------------------ #


class TestSchemaValidatorStructuredFields:
    def test_dtype_mismatch_carries_table_column(self):
        data = {
            "product": pd.DataFrame(
                {"id": ["a"], "name": ["A"], "price": ["not-a-float"]}
            )
        }
        msgs = SchemaValidator([ProductSchema]).validate(data)
        mismatches = [m for m in msgs if m.code == "DTYPE_MISMATCH"]
        assert mismatches, "expected a DTYPE_MISMATCH message"
        assert all(m.table == "product" for m in mismatches)
        assert any(m.column == "price" for m in mismatches)
