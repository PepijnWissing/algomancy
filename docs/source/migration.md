(migration-ref)=
# Migration guide

The 0.6 → 0.8 versions delivered three coordinated overhauls of the ETL
machinery. This page lists the breaking changes together with the
minimal before/after snippets you need to migrate.

## v0.6.0 — Schema API modernization

### `_DATATYPES` → `Column` instances

The new declarative `Column` carries dtype together with optional
metadata (`optional`, `primary_key`, `default`, `nullable`, `unique`,
`description`). The legacy `_DATATYPES` dict still works but emits a
`DeprecationWarning` via `Schema.columns()`.

```{code-block} python
:caption: Before — v0.5
class OrdersSchema(Schema):
    _FILENAME = "orders"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    _DATATYPES = {
        "id": DataType.STRING,
        "qty": DataType.INTEGER,
    }
```

```{code-block} python
:caption: After — v0.6
class OrdersSchema(Schema):
    _FILENAME = "orders"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column(name="id", dtype=DataType.STRING, primary_key=True)
    QTY = Column(name="qty", dtype=DataType.INTEGER)
```

### Classmethod identity accessors

All schema-level accessors are now `@classmethod`, so the call form
gains parentheses:

```{code-block} python
:caption: Before
schema.file_name
schema.extension
schema.datatypes
```

```{code-block} python
:caption: After
schema.file_name()
schema.extension()
schema.datatypes()
```

`get_subschema(key)` now returns a synthetic schema **class**, not an
instance — call its classmethods directly.

## v0.7.0 — Structured validation framework

### `ValidationMessage`: structured location fields

Positional construction `(severity, message)` still works. New optional
keyword fields (`table`, `column`, `row`, `code`) make messages
machine-readable for downstream rendering.

```{code-block} python
:caption: Before
msg = ValidationMessage(ValidationSeverity.ERROR, "bad row 42 in widgets.price")
```

```{code-block} python
:caption: After
msg = ValidationMessage(
    ValidationSeverity.ERROR,
    "bad row",
    table="widgets",
    column="price",
    row=42,
    code="DTYPE_MISMATCH",
)
```

### `ValidationSequence.run_validation()` → `ValidationResult`

```{code-block} python
:caption: Before
is_valid, messages = sequence.run_validation(data)
```

```{code-block} python
:caption: After
result = sequence.run_validation(data)
result.is_valid
result.messages
result.counts_by_severity
result.as_dataframe()
```

### Configurable halt threshold

```{code-block} python
sequence = ValidationSequence(
    [...],
    halt_on=ValidationSeverity.ERROR,  # default is CRITICAL
)
```

### New built-in validators

| Validator | Replaces ad-hoc check |
|---|---|
| `RequiredColumnsValidator` | manual "is column X here?" checks |
| `OptionalColumnGuard` | manual `df[col] = default` lines |
| `PrimaryKeyValidator` | per-project uniqueness/non-null checks |
| `UniqueValueValidator` / `MissingValueValidator` | per-column checks |
| `ForeignKeyValidator` (M5) | per-project FK checks |

## v0.8.0 — Predictable ETL termination

### `ETLPipeline.run()` returns `ETLResult` (no longer raises)

Data-quality failures (validation, missing/malformed files, dtype
conversion errors) arrive as `ETLResult(status='failed')`. Programmer
errors (e.g. `KeyError` from a custom transformer) still propagate.

```{code-block} python
:caption: Before
try:
    datasource = pipeline.run()
except ValidationError as exc:
    report(exc)
```

```{code-block} python
:caption: After
result = pipeline.run()
if result.is_success:
    use(result.datasource)
else:
    report(result.validation_result)
    if result.raised is not None:
        # Expected ETL exception (e.g. FileNotFoundError) was caught
        # and converted; the original is preserved here.
        ...
```

### `DataManager.etl_data()` returns the result

```{code-block} python
:caption: Before
dm.etl_data(files, "orders_2026")  # raised on failure
```

```{code-block} python
:caption: After
result = dm.etl_data(files, "orders_2026")
if result.is_failure:
    show_messages_to_user(result.validation_result.messages)
```

### Conversion failures surface as validation messages

`DataTypeConverter` no longer prints + swallows coercion errors; they
arrive on the final `ValidationResult` as messages with `code="CONVERSION_FAILED"`,
populated `table`/`column`/`row`.

## Bonus: M4 boilerplate reductions

These are not breaking changes — old subclasses keep working — but you
can now delete a lot of plumbing:

- `SimpleETLFactory(schemas)` replaces full `ETLFactory` subclasses for the common case.
- `ETLFactory` ships with default `create_extraction_sequence` / `create_validation_sequence` / `create_transformation_sequence` / `create_loader` implementations; only override the ones you need.
- `DataManager.prepare_files` now drives file-type dispatch off the schema-declared `_EXTENSION`.

See [Extending file types and data types](extending-ref) for the public
`register_extractor` API introduced in M5.
