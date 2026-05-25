(extending-ref)=
# Extending file types and data types

`FileExtension` and `DataType` are `StrEnum`s with a closed default set
(`CSV`, `XLSX`, `JSON` and `STRING`, `INTEGER`, `FLOAT`, `DATETIME`,
`BOOLEAN`, `CATEGORICAL`, `INTERVAL`). User projects can add support
for additional file formats without forking the package by following the
small recipe below.

## 1. Add a new `FileExtension`

`StrEnum`s do not natively allow new members at runtime. The supported
extension pattern is to subclass the enum and use the subclass in your
schemas:

```python
from enum import StrEnum
from algomancy_data import FileExtension


class MyFileExtension(StrEnum):
    PARQUET = "parquet"
```

> Schemas accept any `StrEnum`-derived value via the existing
> `_EXTENSION` field (it is normalised to a string at use sites). Where
> the framework compares against the built-in `FileExtension`, the
> comparison is performed by string equality on the lower-cased value,
> so `MyFileExtension.PARQUET == "parquet"` works as expected.

## 2. Register an extractor for the new extension

Use the public `register_extractor` API to teach the framework how to
extract data for the new `(extension, schema_type)` pair:

```python
from algomancy_data import (
    register_extractor,
    SingleExtractor,
    SchemaType,
)


class ParquetSingleExtractor(SingleExtractor):
    def _extract_file(self):
        import pandas as pd
        return pd.read_parquet(self.file.path)


register_extractor(MyFileExtension.PARQUET, SchemaType.SINGLE, ParquetSingleExtractor)
```

After registration, `ETLFactory.create_extraction_sequence()` (and
therefore `SimpleETLFactory`) will pick up the new extractor for any
schema that declares `_EXTENSION = MyFileExtension.PARQUET`.

## 3. Add a new `DataType` (advanced)

`DataType` values are passed straight through to pandas via
`DataFrame.astype(dtype)`. To support a custom logical type:

1. Subclass `DataType` the same way you subclassed `FileExtension`.
2. Extend `DataTypeConverter` if the new type needs custom coercion
   beyond `astype`. The four built-in helpers
   (`_convert_numeric_column`, `_convert_datetime_column`,
   `_convert_boolean_column`, `_convert_string_column`) are the
   templates to follow; each takes an optional `issues` buffer and a
   `table_name` so dtype-conversion failures surface as
   `CONVERSION_FAILED` validation messages instead of silent NaNs.

If your custom type plugs cleanly into pandas, no converter changes are
needed — the registry-based dispatch handles the rest.

## 4. Confirm the registration

`registered_keys()` returns every `(FileExtension, SchemaType)` pair the
registry knows about, which is useful for sanity-checking at app
startup:

```python
from algomancy_data import registered_keys

assert (MyFileExtension.PARQUET, SchemaType.SINGLE) in registered_keys()
```
