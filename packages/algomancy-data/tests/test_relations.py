"""Tests for the Relation dataclass and schema-to-relations resolver (#113)."""

from algomancy_data import Column, DataType, FileExtension, Schema
from algomancy_data.relations import (
    Relation,
    merge_relations,
    resolve_relations_from_schemas,
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


class OrderSchema(Schema):
    _FILENAME = "order"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column(name="id", dtype=DataType.STRING, primary_key=True)
    PRODUCT_ID = Column(
        name="product_id",
        dtype=DataType.STRING,
        foreign_key=("product", "id"),
        parent_requires_child=True,
    )


class CompositeChildSchema(Schema):
    _FILENAME = "composite_child"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    REGION = Column(
        name="region",
        dtype=DataType.STRING,
        foreign_key=("composite_parent", "region"),
    )
    STORE = Column(
        name="store",
        dtype=DataType.STRING,
        foreign_key=("composite_parent", "store"),
        track_partial_loss=True,
    )
    VAL = Column(name="val", dtype=DataType.FLOAT)


# ------------------------------------------------------------------ #
# Relation dataclass
# ------------------------------------------------------------------ #


class TestRelation:
    def test_construction(self):
        r = Relation(
            child_table="order",
            child_cols=("product_id",),
            parent_table="product",
            parent_cols=("id",),
        )
        assert r.parent_requires_child is False
        assert r.track_partial_loss is False

    def test_key(self):
        r = Relation("a", ("x",), "b", ("y",))
        assert r.key == ("a", ("x",))

    def test_frozen(self):
        import dataclasses
        import pytest

        r = Relation("a", ("x",), "b", ("y",))
        with pytest.raises(dataclasses.FrozenInstanceError):
            r.child_table = "other"  # type: ignore[misc]


# ------------------------------------------------------------------ #
# resolve_relations_from_schemas
# ------------------------------------------------------------------ #


class TestResolveRelations:
    def test_single_fk_derived(self):
        relations = resolve_relations_from_schemas([OrderSchema, ProductSchema])
        assert len(relations) == 1
        r = relations[0]
        assert r.child_table == "order"
        assert r.child_cols == ("product_id",)
        assert r.parent_table == "product"
        assert r.parent_cols == ("id",)
        assert r.parent_requires_child is True
        assert r.track_partial_loss is False

    def test_composite_key_derived(self):
        relations = resolve_relations_from_schemas([CompositeChildSchema])
        assert len(relations) == 1
        r = relations[0]
        assert r.child_table == "composite_child"
        assert r.child_cols == ("region", "store")
        assert r.parent_table == "composite_parent"
        assert r.parent_cols == ("region", "store")
        assert r.track_partial_loss is True

    def test_schema_with_no_fk_yields_no_relation(self):
        relations = resolve_relations_from_schemas([ProductSchema])
        assert relations == []


# ------------------------------------------------------------------ #
# merge_relations
# ------------------------------------------------------------------ #


class TestMergeRelations:
    def test_override_replaces_matching_key(self):
        base = [Relation("order", ("product_id",), "product", ("id",))]
        override = [
            Relation(
                "order",
                ("product_id",),
                "product",
                ("id",),
                parent_requires_child=True,
            )
        ]
        merged = merge_relations(base, override)
        assert len(merged) == 1
        assert merged[0].parent_requires_child is True

    def test_override_appends_new_entries(self):
        base = [Relation("order", ("product_id",), "product", ("id",))]
        override = [Relation("review", ("order_id",), "order", ("id",))]
        merged = merge_relations(base, override)
        assert len(merged) == 2
        keys = {r.key for r in merged}
        assert ("order", ("product_id",)) in keys
        assert ("review", ("order_id",)) in keys

    def test_empty_override_returns_base(self):
        base = [Relation("order", ("product_id",), "product", ("id",))]
        merged = merge_relations(base, [])
        assert len(merged) == 1
        assert merged[0] == base[0]
