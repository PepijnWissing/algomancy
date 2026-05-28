"""Tests for CascadeDropTransformer and CascadeSnapshot (#114, #115)."""

import pandas as pd

from algomancy_data import (
    CascadeDropTransformer,
    CascadeSnapshot,
    Column,
    DataType,
    FileExtension,
    Relation,
    Schema,
    ValidationSeverity,
)
from algomancy_data.schema import SchemaType


# ------------------------------------------------------------------ #
# Schema fixtures
# ------------------------------------------------------------------ #


class ProductSchema(Schema):
    _FILENAME = "product"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column(name="id", dtype=DataType.STRING, primary_key=True)
    NAME = Column(name="name", dtype=DataType.STRING)


class OrderSchema(Schema):
    """Orders point to products; products require ≥1 referencing order."""

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


class ReviewSchema(Schema):
    """Reviews point to orders; nothing required upstream."""

    _FILENAME = "review"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column(name="id", dtype=DataType.STRING, primary_key=True)
    ORDER_ID = Column(
        name="order_id",
        dtype=DataType.STRING,
        foreign_key=("order", "id"),
    )


# ------------------------------------------------------------------ #
# Orphan-child drop
# ------------------------------------------------------------------ #


class TestOrphanChildDrop:
    def test_single_level_orphan_drop(self):
        data = {
            "product": pd.DataFrame({"id": ["P1", "P2"], "name": ["a", "b"]}),
            "order": pd.DataFrame(
                {"id": ["O1", "O2", "O3"], "product_id": ["P1", "P2", "P_GONE"]}
            ),
        }
        # Use only orphan rule (no parent_requires_child)
        t = CascadeDropTransformer(
            extra_relations=[Relation("order", ("product_id",), "product", ("id",))]
        )
        t.transform(data)
        assert list(data["order"]["id"]) == ["O1", "O2"]
        assert any(m.code == "CASCADE_ORPHAN_DROP" for m in t.messages)

    def test_orphan_messages_are_error_severity(self):
        data = {
            "product": pd.DataFrame({"id": ["P1"]}),
            "order": pd.DataFrame({"id": ["O1", "O2"], "product_id": ["P1", "P_GONE"]}),
        }
        t = CascadeDropTransformer(
            extra_relations=[Relation("order", ("product_id",), "product", ("id",))]
        )
        t.transform(data)
        orphan_msgs = [m for m in t.messages if m.code == "CASCADE_ORPHAN_DROP"]
        assert len(orphan_msgs) == 1
        assert orphan_msgs[0].severity == ValidationSeverity.ERROR
        assert orphan_msgs[0].table == "order"
        assert "1 row" in orphan_msgs[0].message

    def test_null_fk_not_dropped(self):
        data = {
            "product": pd.DataFrame({"id": ["P1"]}),
            "order": pd.DataFrame({"id": ["O1", "O2"], "product_id": ["P1", None]}),
        }
        t = CascadeDropTransformer(
            extra_relations=[Relation("order", ("product_id",), "product", ("id",))]
        )
        t.transform(data)
        # The NULL FK row is kept (NULL = "no reference" semantics)
        assert len(data["order"]) == 2

    def test_multi_level_forward_cascade(self):
        """A→B→C: when B rows drop, C orphans should drop on the next pass."""
        data = {
            "product": pd.DataFrame({"id": ["P1"]}),
            "order": pd.DataFrame({"id": ["O1", "O2"], "product_id": ["P1", "P_GONE"]}),
            "review": pd.DataFrame({"id": ["R1", "R2"], "order_id": ["O1", "O2"]}),
        }
        t = CascadeDropTransformer(
            schemas=[ProductSchema, OrderSchema, ReviewSchema],
        )
        t.transform(data)
        # O2 dropped (orphan of products); R2 then orphans of orders
        assert list(data["order"]["id"]) == ["O1"]
        assert list(data["review"]["id"]) == ["R1"]


# ------------------------------------------------------------------ #
# Required-child parent drop
# ------------------------------------------------------------------ #


class TestRequiredChildDrop:
    def test_parent_with_zero_children_dropped(self):
        data = {
            "product": pd.DataFrame({"id": ["P1", "P_LONELY"], "name": ["a", "b"]}),
            "order": pd.DataFrame({"id": ["O1"], "product_id": ["P1"]}),
        }
        t = CascadeDropTransformer(schemas=[ProductSchema, OrderSchema])
        t.transform(data)
        assert list(data["product"]["id"]) == ["P1"]
        codes = {m.code for m in t.messages}
        assert "CASCADE_REQUIRED_CHILD_DROP" in codes

    def test_parent_drop_cascades_to_their_children(self):
        """Dropping P_LONELY shouldn't affect orders, but if P1 is dropped
        because all its orders were already orphaned, downstream tables that
        referenced P1 indirectly should also clean up."""
        data = {
            "product": pd.DataFrame({"id": ["P1"], "name": ["a"]}),
            "order": pd.DataFrame(
                {"id": ["O1"], "product_id": ["P_GONE"]}  # already orphan
            ),
        }
        t = CascadeDropTransformer(schemas=[ProductSchema, OrderSchema])
        t.transform(data)
        # O1 orphaned -> dropped. P1 then has zero children -> dropped.
        assert list(data["order"]["id"]) == []
        assert list(data["product"]["id"]) == []


# ------------------------------------------------------------------ #
# Composite-key FK
# ------------------------------------------------------------------ #


class TestCompositeKey:
    def test_composite_key_orphan_drop(self):
        data = {
            "shop": pd.DataFrame(
                {"region": ["EU", "US"], "store": ["S1", "S2"], "name": ["a", "b"]}
            ),
            "sale": pd.DataFrame(
                {
                    "region": ["EU", "US", "EU"],
                    "store": ["S1", "S2", "S_GONE"],
                    "qty": [1, 2, 3],
                }
            ),
        }
        t = CascadeDropTransformer(
            extra_relations=[
                Relation("sale", ("region", "store"), "shop", ("region", "store"))
            ]
        )
        t.transform(data)
        assert len(data["sale"]) == 2
        assert set(data["sale"]["store"]) == {"S1", "S2"}


# ------------------------------------------------------------------ #
# Schema-derived vs. transformer-override
# ------------------------------------------------------------------ #


class TestRelationMerging:
    def test_extra_relations_override_schema(self):
        # Schema has parent_requires_child=True on order->product, but
        # the user override turns it off via an explicit Relation.
        data = {
            "product": pd.DataFrame({"id": ["P1", "P_LONELY"]}),
            "order": pd.DataFrame({"id": ["O1"], "product_id": ["P1"]}),
        }
        t = CascadeDropTransformer(
            schemas=[ProductSchema, OrderSchema],
            extra_relations=[
                Relation(
                    "order",
                    ("product_id",),
                    "product",
                    ("id",),
                    parent_requires_child=False,  # override the schema flag
                )
            ],
        )
        t.transform(data)
        # P_LONELY should NOT be dropped because the override turned off
        # parent_requires_child.
        assert "P_LONELY" in list(data["product"]["id"])


# ------------------------------------------------------------------ #
# No-op cases
# ------------------------------------------------------------------ #


class PartialLossOrderSchema(Schema):
    """Orders point to products; track_partial_loss on the FK."""

    _FILENAME = "order"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column(name="id", dtype=DataType.STRING, primary_key=True)
    PRODUCT_ID = Column(
        name="product_id",
        dtype=DataType.STRING,
        foreign_key=("product", "id"),
        track_partial_loss=True,
    )


# ------------------------------------------------------------------ #
# Partial-loss (CascadeSnapshot + track_partial_loss=True)
# ------------------------------------------------------------------ #


class TestPartialLoss:
    def test_partial_loss_drops_parent(self):
        """Parent had 2 children at snapshot time; loses 1 → drop parent."""
        before = {
            "product": pd.DataFrame({"id": ["P1"], "name": ["a"]}),
            "order": pd.DataFrame({"id": ["O1", "O2"], "product_id": ["P1", "P1"]}),
        }
        snap = CascadeSnapshot(schemas=[ProductSchema, PartialLossOrderSchema])
        snap.transform(before)

        # Now drop one of P1's orders out-of-band, then run cascade.
        after = {
            "product": pd.DataFrame({"id": ["P1"], "name": ["a"]}),
            "order": pd.DataFrame({"id": ["O1"], "product_id": ["P1"]}),
        }
        t = CascadeDropTransformer(
            schemas=[ProductSchema, PartialLossOrderSchema],
            snapshot=snap,
        )
        t.transform(after)
        assert list(after["product"]["id"]) == []
        codes = {m.code for m in t.messages}
        assert "CASCADE_PARTIAL_LOSS_DROP" in codes

    def test_partial_loss_off_by_default(self):
        """Relation without track_partial_loss=True ignores the snapshot."""
        before = {
            "product": pd.DataFrame({"id": ["P1"]}),
            "order": pd.DataFrame({"id": ["O1", "O2"], "product_id": ["P1", "P1"]}),
        }
        # Use the regular OrderSchema (no track_partial_loss)
        snap = CascadeSnapshot(schemas=[ProductSchema, OrderSchema])
        snap.transform(before)
        assert (
            snap.counts_for(Relation("order", ("product_id",), "product", ("id",)))
            is None
        )

        after = {
            "product": pd.DataFrame({"id": ["P1"]}),
            "order": pd.DataFrame({"id": ["O1"], "product_id": ["P1"]}),
        }
        t = CascadeDropTransformer(
            schemas=[ProductSchema, OrderSchema],
            snapshot=snap,
        )
        t.transform(after)
        # P1 still has 1 child, parent_requires_child satisfied → not dropped
        assert list(after["product"]["id"]) == ["P1"]
        assert all(m.code != "CASCADE_PARTIAL_LOSS_DROP" for m in t.messages)

    def test_snapshot_without_paired_drop_is_noop(self):
        data = {
            "product": pd.DataFrame({"id": ["P1"]}),
            "order": pd.DataFrame({"id": ["O1", "O2"], "product_id": ["P1", "P1"]}),
        }
        snap = CascadeSnapshot(schemas=[ProductSchema, PartialLossOrderSchema])
        snap.transform(data)
        # Data unchanged, no messages emitted by the snapshot.
        assert len(data["product"]) == 1
        assert len(data["order"]) == 2
        assert snap.messages == []

    def test_full_loss_not_partial_loss(self):
        """If parent loses ALL children, that's required-child not partial-loss."""
        before = {
            "product": pd.DataFrame({"id": ["P1"], "name": ["a"]}),
            "order": pd.DataFrame({"id": ["O1", "O2"], "product_id": ["P1", "P1"]}),
        }

        # Schema with both parent_requires_child AND track_partial_loss
        class _S(Schema):
            _FILENAME = "order"
            _EXTENSION = FileExtension.CSV
            _SCHEMA_TYPE = SchemaType.SINGLE
            ID = Column(name="id", dtype=DataType.STRING, primary_key=True)
            PRODUCT_ID = Column(
                name="product_id",
                dtype=DataType.STRING,
                foreign_key=("product", "id"),
                parent_requires_child=True,
                track_partial_loss=True,
            )

        snap = CascadeSnapshot(schemas=[ProductSchema, _S])
        snap.transform(before)

        after = {
            "product": pd.DataFrame({"id": ["P1"], "name": ["a"]}),
            "order": pd.DataFrame({"id": [], "product_id": []}, dtype=object),
        }
        t = CascadeDropTransformer(schemas=[ProductSchema, _S], snapshot=snap)
        t.transform(after)
        codes = [m.code for m in t.messages]
        # zero-children case is required-child, not partial-loss
        assert "CASCADE_REQUIRED_CHILD_DROP" in codes
        assert "CASCADE_PARTIAL_LOSS_DROP" not in codes


class TestPipelineIntegration:
    """End-to-end pipeline run with CascadeDropTransformer wired into SimpleETLFactory."""

    def test_messages_surface_in_etl_result(self, tmp_path):
        """Cascade messages should land on ETLResult.messages (per M3)."""
        from algomancy_data import (
            CSVFile,
            CascadeDropTransformer,
            SimpleETLFactory,
        )

        product_csv = tmp_path / "product.csv"
        order_csv = tmp_path / "order.csv"
        # Built-in CSV extractor uses ';' as the default separator.
        product_csv.write_text("id;name\nP1;a\nP2;b\n", encoding="utf-8")
        order_csv.write_text("id;product_id\nO1;P1\nO2;P_GONE\n", encoding="utf-8")

        factory = SimpleETLFactory(
            schemas=[ProductSchema, OrderSchema],
            transformers=[CascadeDropTransformer(schemas=[ProductSchema, OrderSchema])],
        )
        result = factory.build_pipeline(
            "test_orders",
            files={
                "product": CSVFile(name="product", path=str(product_csv)),
                "order": CSVFile(name="order", path=str(order_csv)),
            },
        ).run()

        assert result.is_success
        cascade_msgs = [
            m for m in result.messages if m.code and m.code.startswith("CASCADE_")
        ]
        assert len(cascade_msgs) >= 1
        assert all(m.severity == ValidationSeverity.ERROR for m in cascade_msgs)

        # Confirm the loaded data is actually cleaned.
        ds_order = result.datasource.get_table("order")
        assert "P_GONE" not in list(ds_order["product_id"])
        # P2 had no orders and parent_requires_child=True → dropped.
        ds_product = result.datasource.get_table("product")
        assert "P2" not in list(ds_product["id"])


class TestNoOps:
    def test_no_relations_no_messages(self):
        data = {"product": pd.DataFrame({"id": ["P1"]})}
        t = CascadeDropTransformer()
        t.transform(data)
        assert t.messages == []
        assert len(data["product"]) == 1

    def test_missing_table_skipped(self):
        # Relation references a table not in data — skip silently.
        data = {"product": pd.DataFrame({"id": ["P1"]})}
        t = CascadeDropTransformer(
            extra_relations=[Relation("order", ("product_id",), "product", ("id",))]
        )
        t.transform(data)
        assert t.messages == []
        assert len(data["product"]) == 1

    def test_clean_data_emits_no_messages(self):
        data = {
            "product": pd.DataFrame({"id": ["P1"], "name": ["a"]}),
            "order": pd.DataFrame({"id": ["O1"], "product_id": ["P1"]}),
        }
        t = CascadeDropTransformer(schemas=[ProductSchema, OrderSchema])
        t.transform(data)
        assert t.messages == []
        assert len(data["product"]) == 1
        assert len(data["order"]) == 1
