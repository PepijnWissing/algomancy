(fundamentals-data-container-ref)=
# Data Source
This document describes the data engine and data sources used in the Algomancy framework. We start with an overview of the 
underlying data container, the `BaseDataSource` class, and then discuss schemas and the ETL process.

## Overview

The `BaseDataSource` class (and its concrete implementation `DataSource`) provides a standardized interface for managing data in Python projects. While `DataSource` is optimized for tabular data using pandas DataFrames, `BaseDataSource` serves as a generic foundation for any domain-specific data model.

A `DataSource` instance contains all necessary information to be processed by an `Algorithm` to produce a `ScenarioResult`. It supports serialization to and from JSON and Parquet formats, enabling easy persistence and transfer of experimental states.

## Description

The framework distinguishes between the abstract `BaseDataSource` and the table-oriented `DataSource`:

- **`BaseDataSource`**: An abstract base class that defines the core identity of a data object, including its unique ID, name, and classification (Master vs. Derived).
- **`DataSource`**: A concrete subclass that stores data in a collection of pandas DataFrames (the `tables` attribute).

### Data Classification
The `ds_type` attribute of a `DataSource` indicates its role in the experimentation lifecycle. Values are members of the `DataClassification` enum:

| Enum Value        | Description                                                                              |
|-------------------|------------------------------------------------------------------------------------------|
| `MASTER_DATA`     | Immutable data tied directly to source files.                                            |
| `DERIVED_DATA`    | Data derived from master data that may be modified during an experiment.                 |
| `DUMMY_DATA`      | Temporary data typically used for testing or demonstration.                              |

### Usage
A standard `DataSource` stores data in its `tables` attribute. The following example demonstrates basic usage:

```python
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

```{note}
While you can create `DataSource` instances directly, they are typically produced by an {ref}`ETL process<etl-ref>`.
```

## Custom Data Source

For most projects, you should create a custom subclass of `BaseDataSource` (or `DataSource`) to encapsulate domain-specific logic and attributes.

To implement a custom data source:
1. **Subclass `BaseDataSource`:** Inherit from the base class.
2. **Implement Serialization:** Override `to_json` and `from_json` to handle your custom attributes.
3. **Handle Derivation:** Optionally override `_post_derive()` to perform logic when data is branched from Master to Derived.

Example of a custom data source:

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


For more details on specific classes, see the {ref}`API reference<datasource-ref>`.