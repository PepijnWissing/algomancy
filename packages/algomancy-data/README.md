### algomancy-data

Data layer for Algomancy dashboards: schemas, extract/transform/load (ETL) primitives, validators, and data containers used by the GUI and scenario packages.

#### Features
- `DataSource` and `BaseDataSource` containers with table management and JSON (de)serialization
- Pluggable ETL pipeline building blocks: `Extractor`, `Transformer`, `Validator`, `Loader`
- `DataManager` orchestrators (stateful/stateless) to drive ETL and manage datasets
- Declarative `InputFileConfiguration` for file inputs (CSV, XLSX, JSON)

#### Installation
```
pip install -e packages/algomancy-data
```

Requires Python >= 3.14. Core dependency: `pandas`.

#### Quick start: use `DataSource` directly
```python
import pandas as pd
from algomancy_data import DataSource, DataClassification

ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="warehouse")
ds.add_table("inventory", pd.DataFrame({"sku": ["A", "B"], "qty": [10, 5]}))

# JSON roundtrip
json_str = ds.to_json()
ds2 = DataSource.from_json(json_str)
assert ds2.get_table("inventory").equals(ds.get_table("inventory"))
```

#### Quick start: orchestrate ETL with a `DataManager`
`DataManager` wires `Extractor` → `Transformer` → `Validator` → `Loader`. You provide an `ETLFactory` that builds these parts for each input configuration.

```python
from typing import List
from algomancy_data import (
    DataSource, DataClassification,
    DataManager, StatelessDataManager, ETLFactory,
    SingleInputFileConfiguration, FileExtension
)

class MyETLFactory(ETLFactory):
    # Implement factory methods to build Extractor/Transformer/Validator/Loader
    ...

input_cfgs: List[SingleInputFileConfiguration] = [
    SingleInputFileConfiguration(
        tag="inventory", file_name="inventory", extension=FileExtension.CSV
    )
]

dm: DataManager = StatelessDataManager(
    etl_factory=MyETLFactory,
    input_configs=input_cfgs,
    save_type="json",  # or other configured type
    data_object_type=DataSource,
)

files = dm.prepare_files(file_items_with_path=[("inventory", "./data/inventory.csv")])
ds: DataSource = dm.etl_data(files=files, dataset_name="warehouse")
```

#### Documentation and examples
- Root docs: `documentation/1_data.md`
- End‑to‑end usage in the example app: `example/` (see `example/data_handling` and `example/main.py`)
