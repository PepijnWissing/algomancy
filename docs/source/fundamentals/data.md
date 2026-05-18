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

For more details on specific classes, see the {ref}`API reference<datasource-ref>`.