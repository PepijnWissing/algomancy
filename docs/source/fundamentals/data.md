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

(data-parameters-ref)=
## Data Parameters

A `BaseDataSource` subclass can declare a typed `BaseParameterSet` that the
framework collects per scenario, persists alongside the algorithm parameters,
and pushes onto the algorithm before `run()`. Use them for knobs that belong
conceptually to the *data* rather than the algorithm — date range, region
filter, category whitelist — so the same algorithm can consume the same data
source under different slices without rewriting either side.

Override `initialize_data_parameters` to declare the shape; the default
returns `EmptyParameters()`, so existing subclasses keep working with no
changes. The method runs on a populated instance, so it can inspect
`self.tables` to derive sensible defaults (e.g. the unique values of a
`category` column).

:::{dropdown} {octicon}`eye` Example: a warehouse data source with two knobs
:color: success
```{code-block} python
:caption: Custom DataSource that declares data parameters
:linenos:
from algomancy_data import DataSource
from algomancy_utils.baseparameterset import (
    BaseParameterSet,
    IntegerParameter,
    MultiEnumParameter,
)


class WarehouseDataParameters(BaseParameterSet):
    def __init__(self, categories: list[str]) -> None:
        super().__init__(name="Warehouse Data")
        self.add_parameters([
            MultiEnumParameter(
                name="category_filter",
                choices=categories or ["(none)"],
                value=list(categories or ["(none)"]),
            ),
            IntegerParameter(name="min_daily_picks", minvalue=0, default=0),
        ])

    def validate(self) -> None:
        pass


class WarehouseDataSource(DataSource):
    def initialize_data_parameters(self) -> BaseParameterSet:
        sku = self.tables.get("sku_data")
        categories = (
            sorted(str(c) for c in sku["category"].dropna().unique())
            if sku is not None and "category" in sku.columns
            else []
        )
        return WarehouseDataParameters(categories=categories)
```
:::

The framework does **not** apply data parameters to the data automatically.
The algorithm reads `self.data_params` and decides whether to act on them —
typically by filtering its input before its main loop. Algorithms that
don't care simply ignore the attribute; the safe access pattern is
`self.data_params.contains("knob_name")` followed by `self.data_params["knob_name"]`.

In the GUI the data parameter card renders next to the algorithm parameter
card in the scenario-creation modal, populated as soon as the user picks a
dataset. Over the HTTP API the descriptor is served by
`GET /api/v1/sessions/{sid}/data/{dataset_key}/parameters`, and supplied
values flow through the `data_params` field of `POST /scenarios`. See
{ref}`Algorithms and Parameters <fundamentals-algorithm-ref>` for the
algorithm-side read pattern.

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
2. **Shared per-sub-table SQL (opt-in).** Each DataFrame the DataSource
   exposes is appended to a single shared SQL table named
   `algomancy_ds__{sub_table}` — one physical table per sub-table *name*,
   reused across every session and dataset. Each row carries
   `_algomancy_session_id` and `_algomancy_dataset_name` discriminator
   columns, so the table count is bounded by the DataSource shape rather
   than growing with sessions × datasets. Data stays externally queryable
   and the DataSource is loaded lazily on `get_data()`. The bundled
   `DataSource` uses this path automatically.

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