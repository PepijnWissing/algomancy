"""Unit tests for M1 schema API — Column field type and Schema accessors."""

import warnings

import pytest

from algomancy_data import Column, DataType, FileExtension, Schema
from algomancy_data.schema import SchemaType


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #


class SingleSchema(Schema):
    _FILENAME = "single"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column(name="id", dtype=DataType.STRING, primary_key=True)
    NAME = Column(name="name", dtype=DataType.STRING)
    SCORE = Column(name="score", dtype=DataType.FLOAT, optional=True)


class LegacySchema(Schema):
    _FILENAME = "legacy"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    _DATATYPES = {
        "id": DataType.STRING,
        "value": DataType.FLOAT,
    }


class MultiSchema(Schema):
    _FILENAME = "multi"
    _EXTENSION = FileExtension.XLSX
    _SCHEMA_TYPE = SchemaType.MULTI

    _DATATYPES = {
        "SheetA": {"col_a": DataType.STRING},
        "SheetB": {"col_b": DataType.INTEGER},
    }


# ------------------------------------------------------------------ #
# Column construction (#73)
# ------------------------------------------------------------------ #


class TestColumn:
    def test_construction(self):
        col = Column(name="col", dtype=DataType.STRING)
        assert col.name == "col"
        assert col.dtype == DataType.STRING

    def test_defaults(self):
        col = Column(name="col", dtype=DataType.INTEGER)
        assert col.optional is False
        assert col.primary_key is False
        assert col.default is None
        assert col.nullable is False
        assert col.unique is False
        assert col.description == ""

    def test_explicit_fields(self):
        col = Column(
            name="col",
            dtype=DataType.FLOAT,
            optional=True,
            primary_key=True,
            default=0.0,
            nullable=True,
            unique=True,
            description="A column",
        )
        assert col.optional is True
        assert col.primary_key is True
        assert col.default == 0.0
        assert col.nullable is True
        assert col.unique is True
        assert col.description == "A column"


# ------------------------------------------------------------------ #
# Cascade / FK metadata on Column (#112)
# ------------------------------------------------------------------ #


class TestColumnCascadeMetadata:
    def test_cascade_field_defaults(self):
        col = Column(name="col", dtype=DataType.STRING)
        assert col.foreign_key is None
        assert col.parent_requires_child is False
        assert col.track_partial_loss is False

    def test_foreign_key_basic(self):
        col = Column(
            name="product_id",
            dtype=DataType.STRING,
            foreign_key=("product", "id"),
        )
        assert col.foreign_key == ("product", "id")
        assert col.parent_requires_child is False
        assert col.track_partial_loss is False

    def test_parent_requires_child_with_fk(self):
        col = Column(
            name="product_id",
            dtype=DataType.STRING,
            foreign_key=("product", "id"),
            parent_requires_child=True,
        )
        assert col.parent_requires_child is True

    def test_track_partial_loss_with_fk(self):
        col = Column(
            name="product_id",
            dtype=DataType.STRING,
            foreign_key=("product", "id"),
            track_partial_loss=True,
        )
        assert col.track_partial_loss is True

    def test_parent_requires_child_without_fk_raises(self):
        with pytest.raises(ValueError, match="parent_requires_child"):
            Column(
                name="col",
                dtype=DataType.STRING,
                parent_requires_child=True,
            )

    def test_track_partial_loss_without_fk_raises(self):
        with pytest.raises(ValueError, match="track_partial_loss"):
            Column(
                name="col",
                dtype=DataType.STRING,
                track_partial_loss=True,
            )


# ------------------------------------------------------------------ #
# Schema.columns() (#74, #75)
# ------------------------------------------------------------------ #


class TestColumns:
    def test_returns_column_mapping(self):
        cols = SingleSchema.columns()
        assert list(cols.keys()) == ["id", "name", "score"]
        assert all(isinstance(v, Column) for v in cols.values())

    def test_column_dtypes(self):
        cols = SingleSchema.columns()
        assert cols["id"].dtype == DataType.STRING
        assert cols["score"].dtype == DataType.FLOAT

    def test_legacy_schema_warns(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            LegacySchema.columns()
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "LegacySchema" in str(w[0].message)

    def test_legacy_schema_builds_columns(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            cols = LegacySchema.columns()
        assert set(cols.keys()) == {"id", "value"}
        assert cols["id"].dtype == DataType.STRING

    def test_multi_schema_raises(self):
        with pytest.raises(TypeError, match="MULTI schema"):
            MultiSchema.columns()


# ------------------------------------------------------------------ #
# required_columns / optional_columns / primary_key (#75)
# ------------------------------------------------------------------ #


class TestAccessors:
    def test_required_columns(self):
        assert SingleSchema.required_columns() == ["id", "name"]

    def test_optional_columns(self):
        assert SingleSchema.optional_columns() == ["score"]

    def test_primary_key_single(self):
        assert SingleSchema.primary_key() == ("id",)

    def test_primary_key_joint(self):
        class JointPK(Schema):
            _FILENAME = "joint"
            _EXTENSION = FileExtension.CSV
            _SCHEMA_TYPE = SchemaType.SINGLE

            A = Column(name="a", dtype=DataType.STRING, primary_key=True)
            B = Column(name="b", dtype=DataType.INTEGER, primary_key=True)
            C = Column(name="c", dtype=DataType.FLOAT)

        assert JointPK.primary_key() == ("a", "b")

    def test_primary_key_empty(self):
        class NoPK(Schema):
            _FILENAME = "nopk"
            _EXTENSION = FileExtension.CSV
            _SCHEMA_TYPE = SchemaType.SINGLE

            X = Column(name="x", dtype=DataType.STRING)

        assert NoPK.primary_key() == ()


# ------------------------------------------------------------------ #
# datatypes() classmethod (#76)
# ------------------------------------------------------------------ #


class TestDatatypes:
    def test_single_column_based(self):
        dt = SingleSchema.datatypes()
        assert dt == {
            "id": DataType.STRING,
            "name": DataType.STRING,
            "score": DataType.FLOAT,
        }

    def test_single_legacy(self):
        dt = LegacySchema.datatypes()
        assert dt == {"id": DataType.STRING, "value": DataType.FLOAT}

    def test_multi_raises(self):
        with pytest.raises(ValueError, match="SINGLE"):
            MultiSchema.datatypes()


# ------------------------------------------------------------------ #
# datatype_groups / sub_names (#76)
# ------------------------------------------------------------------ #


class TestMultiSchema:
    def test_sub_names(self):
        assert MultiSchema.sub_names() == ["SheetA", "SheetB"]

    def test_datatype_groups(self):
        groups = MultiSchema.datatype_groups()
        assert "SheetA" in groups
        assert groups["SheetA"] == {"col_a": DataType.STRING}

    def test_get_subschema_returns_single_class(self):
        sub = MultiSchema.get_subschema("SheetA")
        assert sub.is_single()
        assert sub.datatypes() == {"col_a": DataType.STRING}

    def test_get_subschema_invalid_key(self):
        with pytest.raises(ValueError, match="SheetX"):
            MultiSchema.get_subschema("SheetX")

    def test_single_schema_sub_names_raises(self):
        with pytest.raises(ValueError):
            SingleSchema.sub_names()

    def test_single_schema_datatype_groups_raises(self):
        with pytest.raises(ValueError):
            SingleSchema.datatype_groups()


# ------------------------------------------------------------------ #
# Classmethod identity accessors (#76)
# ------------------------------------------------------------------ #


class TestIdentityAccessors:
    def test_file_name(self):
        assert SingleSchema.file_name() == "single"

    def test_extension(self):
        assert SingleSchema.extension() == FileExtension.CSV

    def test_schema_type(self):
        assert SingleSchema.schema_type() == SchemaType.SINGLE

    def test_file_name_with_extension(self):
        assert SingleSchema.file_name_with_extension() == "single.csv"

    def test_is_single(self):
        assert SingleSchema.is_single()
        assert not SingleSchema.is_multi()

    def test_is_multi(self):
        assert MultiSchema.is_multi()
        assert not MultiSchema.is_single()

    def test_callable_on_instance(self):
        inst = SingleSchema()
        assert inst.file_name() == "single"
        assert inst.datatypes() == {
            "id": DataType.STRING,
            "name": DataType.STRING,
            "score": DataType.FLOAT,
        }
