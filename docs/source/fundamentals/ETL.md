(etl-ref)=
# Extract, Transform, Load

The ETL engine orchestrates the movement of data from source files into a
`DataSource`. It uses small composable **Sequences** for the extraction,
validation, and transformation stages and returns a structured
`ETLResult` you can inspect.

```{important}
Versions 0.6+ introduce a number of API changes covered by the
[migration guide](migration-ref). At a glance: schemas now use `Column`
instances, validators emit structured messages, `ETLPipeline.run()`
returns an `ETLResult` instead of raising, and `SimpleETLFactory` covers
the common zero-subclass case.
```

## Pipeline components

```text
ETLFactory.build_pipeline(name, files, schemas)
        │
        ▼
ExtractionSequence ─▶ ValidationSequence ─▶ TransformationSequence ─▶ Loader
        │                    │                                            │
        └────── dtype coercion ─────── ValidationMessage[] ──────── DataSource
```

`ETLFactory` is a **classmethod-based abstract factory**. Subclasses
override the `create_*` hooks as `@classmethod`s; the factory itself is
never instantiated — the framework passes the class (`type[ETLFactory]`)
around and calls `build_pipeline` on it.

| Component | Role |
|---|---|
| `Schema` | Declares columns, dtypes, primary keys, and the source file metadata. |
| `Extractor` | Reads one file (or one sheet) and applies dtype coercion. |
| `Validator` | Emits structured `ValidationMessage`s against the extracted data. |
| `Transformer` | Reshapes the validated data into the final layout. |
| `Loader` | Materialises the data as a `DataSource`. |
| `ETLFactory` | Composes the four sequences for one dataset. |
| `ETLPipeline` | Runs the composed pipeline and returns an `ETLResult`. |

## Quickstart with `SimpleETLFactory`

For most projects you no longer need to subclass `ETLFactory`.
`SimpleETLFactory` is a concrete classmethod factory: it picks the right
extractors from the registry per schema and ships sensible default
validators (`RequiredColumnsValidator`, `SchemaValidator`, and
`PrimaryKeyValidator`, which self-skips schemas without a primary key).

```{code-block} python
:caption: Zero-subclass ETL pipeline
from algomancy_data import (
    Column,
    DataType,
    FileExtension,
    Schema,
    SimpleETLFactory,
)
from algomancy_data.schema import SchemaType


class OrdersSchema(Schema):
    _FILENAME = "orders"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column(name="id", dtype=DataType.STRING, primary_key=True)
    QTY = Column(name="qty", dtype=DataType.INTEGER)
    DISCOUNT = Column(name="discount", dtype=DataType.FLOAT, optional=True, default=0.0)


schemas = {OrdersSchema.file_name(): OrdersSchema}
result = SimpleETLFactory.build_pipeline(
    "orders_2026", {"orders": orders_file}, schemas
).run()

if result.is_success:
    use(result.datasource)
else:
    for message in result.messages:
        print(message)
```

(fundamentals-schema-ref)=
## Schemas

Schemas are declared with `Column` instances as class attributes. Each
`Column` carries its name, dtype, and optional metadata
(`optional`, `primary_key`, `default`, `nullable`, `unique`,
`description`):

```{code-block} python
:caption: Declaring a Schema
from algomancy_data import Column, DataType, FileExtension, Schema
from algomancy_data.schema import SchemaType


class OrdersSchema(Schema):
    _FILENAME = "orders"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column(name="id", dtype=DataType.STRING, primary_key=True)
    QTY = Column(name="qty", dtype=DataType.INTEGER)
    DATE = Column(name="order_date", dtype=DataType.DATETIME)
```

Use `OrdersSchema.columns()`, `required_columns()`, `optional_columns()`,
and `primary_key()` to introspect the schema. The legacy
`_DATATYPES = {...}` form still works but emits a `DeprecationWarning`.

## Extractors

The framework ships extractors for CSV, JSON, and XLSX (single and
multi-sheet). `ETLFactory.create_extraction_sequence()` picks the right
one for each schema based on a `(FileExtension, SchemaType)` lookup in
the **extractor registry**.

| Extractor | Description |
|---|---|
| `CSVSingleExtractor` | Single table from a CSV. |
| `JSONSingleExtractor` | Single table from a JSON file. |
| `JSONMultiExtractor` | Multiple related tables from a nested JSON file. |
| `XLSXSingleExtractor` | Single sheet from an XLSX file. |
| `XLSXMultiExtractor` | Several sheets from an XLSX file. |
| `DataFrameExtractor` | A pre-built `pandas.DataFrame` — useful in tests and notebooks. |

You only need to override `create_extraction_sequence()` if you need
custom parameters (e.g. a non-default CSV separator):

```{code-block} python
from algomancy_data import (
    CSVSingleExtractor,
    SimpleETLFactory,
)
from algomancy_data.extractor import ExtractionSequence


class MyETLFactory(SimpleETLFactory):
    @classmethod
    def create_extraction_sequence(cls, files=None, schemas=None, logger=None):
        seq = ExtractionSequence(logger=logger)
        seq.add_extractor(
            CSVSingleExtractor(
                file=files["orders"],
                schema=schemas["orders"],
                separator=",",
                logger=logger,
            )
        )
        return seq
```

(nested-json-ref)=
### Nested JSON into related tables

`JSONSingleExtractor` flattens nested **objects** with dot notation, but a
nested **list of objects** (e.g. an `Orders` array on each `Customer`)
collapses to a single opaque cell. For documents like that, declare a
`MULTI` schema with one `ColumnGroup` per output table and let
`JSONMultiExtractor` split the document for you.

Each `ColumnGroup` carries a `source_path` saying where its rows live
relative to a top-level record:

- `source_path=()` — the **root/parent** group. Each top-level record
  contributes one row. Exactly one group must use this.
- `source_path=("PickOrderLines",)` — a **child** group. Each parent
  record's `PickOrderLines` list is exploded into this group's rows.
- A child column with
  `foreign_key=(parent_group_name, parent_pk_column)` is populated
  automatically from the parent's primary key at extraction time. The
  same declaration is consumed by `ForeignKeyValidator` and
  `CascadeDropTransformer`.

The top-level JSON can be either a list of records, or a dict with
exactly one list-valued key (the wrapper is unwrapped automatically).

```{code-block} python
:caption: Splitting `PickLoadCarriers` and `PickOrderLines` into two tables
from algomancy_data import (
    Column,
    ColumnGroup,
    DataType,
    FileExtension,
    Schema,
    SimpleETLFactory,
)
from algomancy_data.schema import SchemaType


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


schemas = {PickLoadCarrierSchema.file_name(): PickLoadCarrierSchema}
result = SimpleETLFactory.build_pipeline(
    "today", {"picks": picks_file}, schemas
).run()
# result.datasource.tables ->
#   "picks.PickLoadCarriers": flat parent table (no PickOrderLines column)
#   "picks.PickOrderLines":   one row per order line, with PickLoadCarrierIdentity FK
```

```{tip}
`JSONMultiExtractor` validates the schema eagerly: it requires exactly one
root group, and child FK columns must reference a real parent column.
Misconfigurations raise at extractor construction, not at run time.
```

To support a new file format, see
[Extending file types and data types](extending-ref).

## Validators

Validators emit `ValidationMessage`s with structured location fields
(`table`, `column`, `row`, `code`). The `ValidationSequence` aggregates
them and returns a `ValidationResult` whose `is_valid` is governed by a
configurable `halt_on` severity (default `CRITICAL`).

Built-in validators:

| Validator | Purpose |
|---|---|
| `RequiredColumnsValidator` | Every required column is present per schema. |
| `SchemaValidator` | dtype + unexpected-column check per schema. |
| `PrimaryKeyValidator` | Uniqueness + non-null over each `primary_key`. |
| `UniqueValueValidator` / `MissingValueValidator` | Per-column unique / null checks. |
| `ForeignKeyValidator` | Cross-table referential integrity. |
| `ExtractionSuccessVerification` | Each extracted DataFrame is non-empty. |

The defaults from `ETLFactory.create_validation_sequence()` already
cover the most common needs; add your own with:

```{code-block} python
from algomancy_data import (
    ForeignKeyValidator,
    SimpleETLFactory,
    ValidationSeverity,
)


class MyETLFactory(SimpleETLFactory):
    @classmethod
    def create_validation_sequence(cls, schemas, logger=None):
        seq = super().create_validation_sequence(schemas, logger)
        seq.add_validator(
            ForeignKeyValidator("order_lines", "product_id", "products", "id")
        )
        seq.halt_on = ValidationSeverity.ERROR
        return seq
```

### Writing a custom validator

```{code-block} python
from algomancy_data import Validator, ValidationSeverity


class NonNegativeQuantityValidator(Validator):
    def __init__(self, table: str, column: str = "qty") -> None:
        super().__init__()
        self.table = table
        self.column = column

    def validate(self, data):
        df = data[self.table]
        negatives = df.index[df[self.column] < 0].tolist()
        for row in negatives:
            self.add_message(
                ValidationSeverity.ERROR,
                f"Negative quantity in {self.table}.{self.column}",
                table=self.table,
                column=self.column,
                row=int(row),
                code="NEGATIVE_QTY",
            )
        return self.messages
```

## Transformers

Transformers run after validation succeeds and reshape the data into the
form expected downstream. The framework provides:

| Transformer | Purpose |
|---|---|
| `NoopTransformer` | Pass-through; no changes. |
| `CleanTransformer` | dropna + lowercase columns. |
| `JoinTransformer` | Joins tables together. |
| `OptionalColumnGuard` | Injects missing optional columns using `Column.default`. |

Subclass `Transformer` for project-specific reshaping.

```{important}
Programmer errors raised from inside a transformer (`KeyError`,
`AttributeError`, `TypeError` …) propagate from `ETLPipeline.run()` — they
are not converted to `ETLResult(status='failed')` because they indicate
real defects rather than data-quality issues.
```

(cascade-cleanup-ref)=
## Relational cascade cleanup

Real-world input data is often incomplete: an order may reference a
product that wasn't in the latest export, a parent record may have lost
all its children mid-pipeline, and so on. The `CascadeDropTransformer`
declaratively cleans up such inconsistencies by walking foreign-key
relations declared on your schemas and dropping rows whose references
are unsatisfied. Drops surface as aggregated `ValidationMessage`s with
`Severity.ERROR` — visible but non-halting by default.

### Declaring relations on `Column`

Foreign-key relations live on the **child** column. Two opt-in flags
control parent-side cascade behavior:

| Field | Purpose |
|---|---|
| `foreign_key=(parent_table, parent_col)` | Declares the FK reference. |
| `parent_requires_child=True` | Drop the parent when it has zero referencing children on this relation. |
| `track_partial_loss=True` | Enable partial-loss detection (drop the parent when it loses *some* of its children mid-pipeline). Requires a paired `CascadeSnapshot`. |

```{code-block} python
:caption: Schemas with FK declarations
from algomancy_data import Column, DataType, FileExtension, Schema
from algomancy_data.schema import SchemaType


class ProductSchema(Schema):
    _FILENAME = "product"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column(name="id", dtype=DataType.STRING, primary_key=True)


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
```

### The three drop rules

`CascadeDropTransformer.transform(data)` iterates to fixpoint, applying
on each pass:

| Rule | Code | Trigger |
|---|---|---|
| Orphan-child drop | `CASCADE_ORPHAN_DROP` | Child row's FK is not in the parent's referenced column set. Always on. |
| Required-child parent drop | `CASCADE_REQUIRED_CHILD_DROP` | Parent row has zero referencing children. Opt-in via `parent_requires_child=True`. |
| Partial-loss parent drop | `CASCADE_PARTIAL_LOSS_DROP` | Parent row lost *some* (but not all) of its children vs. a baseline snapshot. Opt-in via `track_partial_loss=True` **and** a paired `CascadeSnapshot`. |

NULL values in an FK column are treated as "no reference" and never
trigger an orphan drop. Combine with `nullable=False` on the column if
you want NULLs to be rejected by `MissingValueValidator` instead.

### Wiring it into the pipeline

`CascadeDropTransformer` is a regular `Transformer` — add it to the
transformation sequence:

```{code-block} python
:caption: Cascade cleanup in a SimpleETLFactory subclass
from algomancy_data import (
    CascadeDropTransformer,
    SimpleETLFactory,
)
from algomancy_data.transformer import TransformationSequence


class CascadeFactory(SimpleETLFactory):
    @classmethod
    def create_transformation_sequence(cls, schemas=None, logger=None):
        seq = TransformationSequence(logger=logger)
        seq.add_transformer(
            CascadeDropTransformer(schemas=[ProductSchema, OrderSchema])
        )
        return seq


schemas = {s.file_name(): s for s in (ProductSchema, OrderSchema)}
result = CascadeFactory.build_pipeline("orders_2026", files, schemas).run()

for message in result.messages:
    if message.code and message.code.startswith("CASCADE_"):
        print(message)
# e.g. "ERROR: 3 row(s) dropped from 'order' by CASCADE_ORPHAN_DROP …"
```

### Partial-loss with `CascadeSnapshot`

Partial-loss detection compares the current child-counts to a baseline
captured **before** any drop-capable transformer runs. Place a
`CascadeSnapshot` early in the transformation sequence and pass it to
the cascade transformer:

```{code-block} python
from algomancy_data import CascadeDropTransformer, CascadeSnapshot, SimpleETLFactory
from algomancy_data.transformer import TransformationSequence


class SnapshotFactory(SimpleETLFactory):
    @classmethod
    def create_transformation_sequence(cls, schemas=None, logger=None):
        snapshot = CascadeSnapshot(schemas=[ProductSchema, OrderSchema])
        seq = TransformationSequence(logger=logger)
        seq.add_transformer(snapshot)
        # ... any user transformers that may drop rows go here ...
        seq.add_transformer(
            CascadeDropTransformer(
                schemas=[ProductSchema, OrderSchema],
                snapshot=snapshot,
            )
        )
        return seq
```

The snapshot is a no-op on data — it only records baselines — so it is
safe to leave in place even when no other transformer drops rows.

### Overriding schema-derived relations

If you need to add or override a relation without changing the schema,
pass `extra_relations=` to the transformer. Overrides match on
`(child_table, child_cols)` and replace any schema-derived entry with
the same key:

```{code-block} python
from algomancy_data import CascadeDropTransformer, Relation

CascadeDropTransformer(
    schemas=[ProductSchema, OrderSchema],
    extra_relations=[
        Relation("order", ("product_id",), "product", ("id",),
                 parent_requires_child=False),  # turn the schema flag off
    ],
)
```

### Auto-wiring `ForeignKeyValidator` from the same declarations

`ForeignKeyValidator.from_schemas([...])` returns one validator per
relation, derived from the same `Column.foreign_key` declarations. Use
it together with `CascadeDropTransformer` so that violations are
reported (validator) and cleaned (transformer) without duplicating the
relation list:

```{code-block} python
from algomancy_data import ForeignKeyValidator

validators = ForeignKeyValidator.from_schemas([ProductSchema, OrderSchema])
```

## Loader

`DataSourceLoader` is the default and produces a `DataSource` whose
`validation_messages` carry the messages collected during validation.
Subclass `Loader` if you need a custom destination type.

## `ETLPipeline.run()` and `ETLResult`

`ETLPipeline.run()` never raises on data-quality problems. Instead it
returns an `ETLResult`:

```{code-block} python
@dataclass
class ETLResult:
    status: Literal["success", "failed"]
    datasource: BaseDataSource | None
    validation_result: ValidationResult | None
    raised: Exception | None
```

Convenience accessors: `result.is_success`, `result.is_failure`,
`result.messages`, and `result.validation_result.as_dataframe()`.

## Putting it all together

```{code-block} python
from algomancy_data import (
    Column,
    DataType,
    FileExtension,
    ForeignKeyValidator,
    Schema,
    SimpleETLFactory,
)
from algomancy_data.schema import SchemaType


class OrdersSchema(Schema):
    _FILENAME = "orders"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column(name="id", dtype=DataType.STRING, primary_key=True)
    PRODUCT_ID = Column(name="product_id", dtype=DataType.STRING)


class ProductsSchema(Schema):
    _FILENAME = "products"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column(name="id", dtype=DataType.STRING, primary_key=True)


class OrdersFactory(SimpleETLFactory):
    @classmethod
    def create_validation_sequence(cls, schemas, logger=None):
        seq = super().create_validation_sequence(schemas, logger)
        seq.add_validator(
            ForeignKeyValidator("orders", "product_id", "products", "id")
        )
        return seq


schemas = {s.file_name(): s for s in (OrdersSchema, ProductsSchema)}
result = OrdersFactory.build_pipeline("Q1", files, schemas).run()
```
