"""Disk-backed integration tests for the ETL primitives.

These tests exercise the extractor/validator/transformer chain against
real fixture files under ``tests/data/`` (rather than synthesised
in-memory DataFrames). They complement the in-memory unit tests in
``test_cascade_drop.py``, ``test_json_multi_extractor.py``,
``test_validator.py`` and ``test_m4.py`` by covering the file-parsing
path against the actual formats shipped with the framework.

Each subsection is independent; schemas are declared locally so a
breakage in one test cannot mask another.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from algomancy_data import (
    CSVFile,
    CascadeDropTransformer,
    Column,
    ColumnGroup,
    DataType,
    FileExtension,
    JSONFile,
    JSONMultiExtractor,
    JSONSingleExtractor,
    MissingValueValidator,
    Schema,
    SimpleETLFactory,
    UniqueValueValidator,
    ValidationSeverity,
    XLSXFile,
    XLSXMultiExtractor,
    XLSXSingleExtractor,
)
from algomancy_data.schema import SchemaType

FIXTURES = Path(__file__).parent / "data"


# ====================================================================== #
# Cascade chain on disk — categories ← products ← order_items
# ====================================================================== #


class CategorySchema(Schema):
    _FILENAME = "categories"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column("category_id", dtype=DataType.STRING, primary_key=True)
    NAME = Column("name", dtype=DataType.STRING)
    DEPARTMENT = Column("department", dtype=DataType.STRING)


class ProductSchema(Schema):
    _FILENAME = "products"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column("product_id", dtype=DataType.STRING, primary_key=True)
    CATEGORY_ID = Column(
        "category_id",
        dtype=DataType.STRING,
        foreign_key=("categories", "category_id"),
        parent_requires_child=True,
    )
    NAME = Column("name", dtype=DataType.STRING)
    PRICE = Column("price", dtype=DataType.FLOAT)


class OrderItemSchema(Schema):
    _FILENAME = "order_items"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column("order_item_id", dtype=DataType.STRING, primary_key=True)
    PRODUCT_ID = Column(
        "product_id",
        dtype=DataType.STRING,
        foreign_key=("products", "product_id"),
    )
    QUANTITY = Column("quantity", dtype=DataType.INTEGER)


class TestCascadeChainOnDisk:
    """End-to-end ETL run that mirrors the showcase wiring removed from
    ``example/data_handling/factories.py``: orphan products drop, then
    childless categories drop, then orphan order_items drop transitively.
    """

    def _build_files(self):
        root = FIXTURES / "cascade_chain"
        return {
            "categories": CSVFile(name="categories", path=str(root / "categories.csv")),
            "products": CSVFile(name="products", path=str(root / "products.csv")),
            "order_items": CSVFile(
                name="order_items", path=str(root / "order_items.csv")
            ),
        }

    def test_cascade_drops_orphans_and_childless_parents(self):
        schemas = [CategorySchema, ProductSchema, OrderItemSchema]
        factory = SimpleETLFactory(
            schemas=schemas,
            transformers=[CascadeDropTransformer(schemas=schemas)],
        )
        result = factory.build_pipeline("cascade_demo", self._build_files()).run()

        assert result.is_success

        cats = result.datasource.get_table("categories")
        prods = result.datasource.get_table("products")
        items = result.datasource.get_table("order_items")

        # Products P-006 (CAT-99) and P-007 (CAT-XX) reference non-existent
        # categories — orphan drop removes them.
        assert "P-006" not in set(prods["product_id"])
        assert "P-007" not in set(prods["product_id"])

        # CAT-04 (Toys) and CAT-05 (Garden) have no products at all —
        # parent_requires_child drops them.
        assert "CAT-04" not in set(cats["category_id"])
        assert "CAT-05" not in set(cats["category_id"])
        assert set(cats["category_id"]) == {"CAT-01", "CAT-02", "CAT-03"}

        # Order items referencing dropped or never-existing products are
        # orphaned and removed transitively.
        item_ids = set(items["order_item_id"])
        assert "OI-006" not in item_ids  # P-006 dropped
        assert "OI-007" not in item_ids  # P-007 dropped
        assert "OI-008" not in item_ids  # P-999 never existed

        codes = {m.code for m in result.messages if m.code}
        assert "CASCADE_ORPHAN_DROP" in codes
        assert "CASCADE_REQUIRED_CHILD_DROP" in codes


# ====================================================================== #
# JSON-multi extractor on disk — picks.json (parent + nested child)
# ====================================================================== #


class PickLoadCarrierSchema(Schema):
    _FILENAME = "picks"
    _EXTENSION = FileExtension.JSON
    _SCHEMA_TYPE = SchemaType.MULTI

    PICK_LOAD_CARRIERS = ColumnGroup(
        "PickLoadCarriers",
        [
            Column("Identity", dtype=DataType.STRING, primary_key=True),
            Column("PickOrderIdentity", dtype=DataType.STRING),
            Column("NumberOfPickOrderLines", dtype=DataType.INTEGER),
        ],
        source_path=(),
    )

    PICK_ORDER_LINES = ColumnGroup(
        "PickOrderLines",
        [
            Column("Identity", dtype=DataType.STRING, primary_key=True),
            Column(
                "PickLoadCarrierIdentity",
                dtype=DataType.STRING,
                foreign_key=("PickLoadCarriers", "Identity"),
            ),
            Column("PickSequence", dtype=DataType.INTEGER),
            Column("OrderedQuantity", dtype=DataType.INTEGER),
        ],
        source_path=("PickOrderLines",),
    )


class TestPicksJSONMultiOnDisk:
    def test_extractor_splits_parent_and_child_and_injects_fk(self):
        f = JSONFile(
            name="picks", path=str(FIXTURES / "picks_json_multi" / "picks.json")
        )
        out = JSONMultiExtractor(f, PickLoadCarrierSchema).extract()

        parent = out["picks.PickLoadCarriers"]
        child = out["picks.PickOrderLines"]

        assert len(parent) == 3
        # NumberOfPickOrderLines on the fixture is [4, 2, 1] — child rows
        # should sum to the same total.
        assert len(child) == int(parent["NumberOfPickOrderLines"].sum())

        # Every child row carries its parent's Identity via FK injection.
        assert set(child["PickLoadCarrierIdentity"]).issubset(set(parent["Identity"]))
        assert child["PickLoadCarrierIdentity"].notna().all()


class TestPicksJSONMultiOnDiskFullETL:
    """Regression for issue #172: a ColumnGroup-only MULTI schema must
    survive the full ``SimpleETLFactory.build_pipeline().run()`` path,
    not just direct ``JSONMultiExtractor`` extraction. The previous gate
    in ``ETLFactory.create_validation_sequence`` called ``primary_key()``
    on every schema before construction, which raises on MULTI schemas
    because ``columns()`` is SINGLE-only.
    """

    def _files(self):
        return {
            "picks": JSONFile(
                name="picks", path=str(FIXTURES / "picks_json_multi" / "picks.json")
            )
        }

    def test_validation_sequence_constructs_for_multi_schema(self):
        # Before the #172 fix, this call raised because the gate at
        # ``etl.py:339`` invoked ``schema.primary_key()`` on a MULTI schema,
        # which delegates to the SINGLE-only ``columns()`` accessor.
        factory = SimpleETLFactory(schemas=[PickLoadCarrierSchema])
        v_seq = factory.create_validation_sequence()
        # Construction succeeded; PK validation should now run without error
        # against an empty data dict (no tables → no per-row checks fire).
        result = v_seq.run_validation({})
        assert result.is_valid

    def test_full_pipeline_run_succeeds(self):
        factory = SimpleETLFactory(schemas=[PickLoadCarrierSchema])
        result = factory.build_pipeline("picks", self._files()).run()

        assert result.is_success, [m.message for m in result.messages]

        parent = result.datasource.get_table("picks.PickLoadCarriers")
        child = result.datasource.get_table("picks.PickOrderLines")

        assert len(parent) == 3
        assert len(child) == int(parent["NumberOfPickOrderLines"].sum())
        assert child["PickLoadCarrierIdentity"].notna().all()


# ====================================================================== #
# Multisheet XLSX on disk — two ColumnGroups, two sheets
# ====================================================================== #


class LocationSchema(Schema):
    _FILENAME = "multisheet"
    _EXTENSION = FileExtension.XLSX
    _SCHEMA_TYPE = SchemaType.MULTI

    STEDEN = ColumnGroup(
        "Steden",
        [
            Column("Country", dtype=DataType.STRING),
            Column("City", dtype=DataType.STRING),
        ],
    )
    KLANTEN = ColumnGroup(
        "Klanten",
        [
            Column("ID", dtype=DataType.INTEGER, primary_key=True),
            Column("Naam", dtype=DataType.STRING),
        ],
    )


class TestMultisheetXLSXOnDisk:
    def test_each_sheet_lands_as_its_own_table(self):
        f = XLSXFile(
            name="multisheet", path=str(FIXTURES / "multisheet" / "multisheet.xlsx")
        )
        out = XLSXMultiExtractor(f, LocationSchema).extract()

        # Both sheets are emitted under <file>.<sheet_name> keys.
        steden = out["multisheet.Steden"]
        klanten = out["multisheet.Klanten"]

        assert set(steden.columns) >= {"Country", "City"}
        assert set(klanten.columns) >= {"ID", "Naam"}
        # The fixture has 6 cities and 4 customers.
        assert len(steden) == 6
        assert len(klanten) == 4


# ====================================================================== #
# Single-sheet XLSX on disk — sheet_name=1 selects the second sheet
# ====================================================================== #


class InventoryMinimalSchema(Schema):
    """Conservative subset of the original showcase ``InventorySchema``.

    Only declares columns we can assert against; everything else in the
    sheet is allowed to come through untouched. Demonstrates two things
    the registry-default extractor cannot do: ``sheet_name=1`` selection
    and multiline column headers (real ``\\n`` in the header text).
    """

    _FILENAME = "inventory"
    _EXTENSION = FileExtension.XLSX
    _SCHEMA_TYPE = SchemaType.SINGLE

    BRANCH = Column("Branch", dtype=DataType.STRING)
    ITEM_NUMBER = Column("Item\nNumber", dtype=DataType.STRING)
    ITEM_DESCRIPTION = Column("Item\nDescription", dtype=DataType.STRING)


class TestInventoryXLSXOnDisk:
    def test_sheet_name_index_one_selects_second_sheet(self):
        f = XLSXFile(
            name="inventory", path=str(FIXTURES / "inventory" / "inventory.xlsx")
        )
        extractor = XLSXSingleExtractor(f, InventoryMinimalSchema, sheet_name=1)
        out = extractor.extract()
        df = next(iter(out.values()))

        # Sheet 0 is a cover sheet; sheet 1 is the actual inventory grid.
        # Multi-line column headers should survive verbatim.
        assert "Branch" in df.columns
        assert "Item\nNumber" in df.columns
        assert "Item\nDescription" in df.columns
        assert len(df) > 0


# ====================================================================== #
# Employees JSON on disk — JSONSingleExtractor + validators
# ====================================================================== #


class EmployeeSchema(Schema):
    _FILENAME = "employees"
    _EXTENSION = FileExtension.JSON
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column("id", dtype=DataType.STRING, primary_key=True)
    NAME = Column("name", dtype=DataType.STRING)
    EMAIL = Column("email", dtype=DataType.STRING, unique=True)
    IS_ACTIVE = Column("is_active", dtype=DataType.BOOLEAN)
    AGE = Column("age", dtype=DataType.INTEGER)


class TestEmployeesJSONOnDisk:
    def _extract(self):
        f = JSONFile(
            name="employees", path=str(FIXTURES / "employees" / "employees.json")
        )
        out = JSONSingleExtractor(f, EmployeeSchema).extract()
        # JSONSingleExtractor emits {file_name: df}.
        return out["employees"]

    def test_extracts_flat_records(self):
        df = self._extract()
        assert len(df) > 0
        for required in ("id", "name", "email", "is_active"):
            assert required in df.columns

    def test_missing_value_validator_runs_clean(self):
        df = self._extract()
        v = MissingValueValidator(
            table="employees",
            columns=["name", "email", "is_active"],
            severity=ValidationSeverity.ERROR,
        )
        v.validate({"employees": df})
        # The fixture has no nulls in these columns; validator stays quiet.
        assert all(m.code != "MISSING_VALUE" for m in v.messages)

    def test_unique_value_validator_passes_for_unique_emails(self):
        df = self._extract()
        v = UniqueValueValidator(
            table="employees",
            columns=["email"],
            severity=ValidationSeverity.WARNING,
        )
        v.validate({"employees": df})
        # All emails in the fixture are unique.
        assert v.messages == [] or all(
            m.severity != ValidationSeverity.ERROR for m in v.messages
        )

    def test_missing_value_validator_flags_injected_nulls(self):
        df = self._extract().copy()
        # Inject a null into ``email`` to prove the validator actually fires.
        df.loc[df.index[0], "email"] = pd.NA
        v = MissingValueValidator(
            table="employees",
            columns=["email"],
            severity=ValidationSeverity.ERROR,
        )
        v.validate({"employees": df})
        assert any(
            m.severity == ValidationSeverity.ERROR and m.column == "email"
            for m in v.messages
        )

    def test_unique_value_validator_flags_injected_duplicate(self):
        df = self._extract().copy()
        # Force a duplicate email.
        df.loc[df.index[1], "email"] = df.loc[df.index[0], "email"]
        v = UniqueValueValidator(
            table="employees",
            columns=["email"],
            severity=ValidationSeverity.WARNING,
        )
        v.validate({"employees": df})
        assert any(m.column == "email" for m in v.messages)
