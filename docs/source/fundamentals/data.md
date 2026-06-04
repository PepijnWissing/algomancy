(fundamentals-data-container-ref)=
# Data Source
This document describes the data engine and data sources used in the Algomancy framework. We start with an overview of the 
underlying data container, the `BaseDataSource` class, and then discuss schemas and the ETL process.

## Description

The abstract `BaseDataSource` class serves as a generic foundation for any domain-specific data model. It contains the
core identity of a data object, including its unique ID, name, and classification (Master vs. Derived), as well as 
internal behavior for data management.

The `DataSource` class is a reasonably generic, table-oriented implementation of `BaseDataSource` for tabular 
data using pandas DataFrames. A `DataSource` instance contains all necessary information to be processed by an `Algorithm`
to produce a `ScenarioResult`. It supports serialization to and from JSON and Parquet formats, enabling easy persistence 
and transfer of experimental states.

In an Algomancy app, data can exist in either one of two states:
- Master data: Immutable data tied directly to source files. 
- Derived data: Data derived from master data that may be modified. 

Data is assigned the `MASTER_DATA` classification if it is constructed by an ETL process or saved by the `save` usecase.
The `derive` usecase creates a copy of an existing dataset and assigns it the classification `DERIVED_DATA`. Data that 
was serialized (`download`-ed) and deserialized (`upload`-ed) maintains its classification. 

:::{dropdown} {octicon}`eye` Example usage
:color: success
A standard `DataSource` stores data in its `tables` attribute. The following example demonstrates basic usage:

```{code-block} python
:caption: Example usage of DataSource
:linenos:
from algomancy_data import DataSource, DataClassification
import pandas as pd

# Create a DataSource instance
ds = DataSource(DataClassification.MASTER_DATA, name="MyDataSource")

# Add a table
df = pd.DataFrame({'col1': [1, 2], 'col2': ['A', 'B']})
ds.add_table('my_table', df)

# Retrieve a table
retrieved_df = ds.get_table('my_table') 
```
:::

```{note}
While you can create `DataSource` instances directly, they are typically produced by an {ref}`ETL process<etl-ref>`.
```

## Custom Data Source

For most projects, you should create a custom subclass of `BaseDataSource` (or `DataSource`) to encapsulate domain-specific logic and attributes.

To implement a custom data source:
1. **Subclass `BaseDataSource`:** Inherit from the base class.
2. **Implement Serialization:** Override `to_json` and `from_json` to handle your custom attributes.
3. (_Optional_) Handle Derivation: override `_post_derive()` to perform logic when data is branched from Master to Derived.

:::{dropdown} {octicon}`eye` Example of a custom data source
:color: success
```python 
from algomancy_data import BaseDataSource, DataClassification
from dataclasses import dataclass
import json

@dataclass
class Location:
    name: str
    lat: float
    lon: float

class MyCustomSource(BaseDataSource):
    def __init__(self, ds_type, name, locations: dict[str, Location] = None):
        super().__init__(ds_type, name)
        self.locations = locations or {}

    def to_json(self) -> str:
        # Custom serialization logic
        return json.dumps({
            "ds_type": self.ds_type,
            "name": self.name,
            "locations": {k: vars(v) for k, v in self.locations.items()}
        })

    @classmethod
    def from_json(cls, json_string: str) -> 'MyCustomSource':
        data = json.loads(json_string)
        locations = {k: Location(**v) for k, v in data["locations"].items()}
        return cls(data["ds_type"], data["name"], locations)
```
:::

## Database persistence

When the framework runs with `persistence_backend="database"` (see
{ref}`Sessions <fundamentals-sessions-ref>`), the `DatabaseDataManager`
persists every `DataSource` through whichever `data_object_type` was wired
into `CoreConfig`. It chooses between two storage paths per DataSource:

1. **JSON blob (universal default).** The full DataSource is serialised via
   its `to_json()` and stored in a `payload` column on the catalogue table.
   Any `BaseDataSource` subclass works out of the box — the only requirement
   is the abstract `to_json` / `from_json` pair every subclass already has
   to implement.
2. **Per-sub-table SQL (opt-in).** Each DataFrame the DataSource exposes
   becomes its own SQL table, named
   `ds__{session_id}__{dataset_name}__{sub_table}`. The data stays
   externally queryable and the DataSource is loaded lazily on
   `get_data()`. The bundled `DataSource` uses this path automatically.

To opt a custom subclass into the per-table path, implement the
{ref}`SqlTableLayout <sql-table-layout-ref>` protocol. That is: implement the
`to_sql_tables()` and `from_sql_tables()` functions. A si

```python
from algomancy_data import BaseDataSource, DataClassification
from algomancy_data.database import SqlTableLayout  # noqa: F401  (for type hints only)
import pandas as pd

class MyTabularSource(BaseDataSource):
    def __init__(self, ds_type, name, **kwargs):
        super().__init__(ds_type, name, **kwargs)
        self._tables: dict[str, pd.DataFrame] = {}

    # ---- SqlTableLayout protocol ----
    def to_sql_tables(self) -> dict[str, pd.DataFrame]:
        return self._tables

    def from_sql_tables(self, tables: dict[str, pd.DataFrame]) -> None:
        self._tables.update(tables)

    # ---- BaseDataSource (still required) ----
    def to_json(self) -> str: ...
    @classmethod
    def from_json(cls, payload: str) -> "MyTabularSource": ...
```

If a subclass doesn't implement these two methods, persistence falls back
to the JSON-blob path automatically — nothing else changes. Pick the
per-table path when external SQL queryability or memory-efficient lazy
loading of large DataFrames matters; pick the default JSON-blob path when
the DataSource holds non-tabular state or you want the simplest possible
contract.

For more details on specific classes, see the {ref}`API reference<datasource-ref>`.