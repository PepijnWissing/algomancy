(tutorial-etl-ref)=
# Data intake
An Algomancy app reads data through an {ref}`ETL<etl-ref>` pipeline.
The quickstart wizard has already generated the folder structure, schemas, and ETL factory for us.
In this section we review the generated files, then write the custom transformation and loading logic for the TSP model.

## Review the generated schemas

Open `src/data_handling/generated_schemas.py`. The wizard scanned the three input files and created a {ref}`Schema<fundamentals-schema-ref>` subclass for each one, with inferred column names and types:

:::{dropdown} {octicon}`code` Code
:color: info

```{code-block} python
:caption: `generated_schemas.py` (as generated)
:linenos:
from typing import Dict
from algomancy_data import Schema, DataType, FileExtension
from algomancy_data.schema import SchemaType


class DcSchema(Schema):
    _FILENAME = "dc"
    _EXTENSION = FileExtension.XLSX
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = "ID"
    X = "x"
    Y = "y"

    def _defined_datatypes(self) -> Dict[str, DataType]:
        return {
            DcSchema.ID: DataType.STRING,
            DcSchema.X: DataType.INTEGER,
            DcSchema.Y: DataType.INTEGER,
        }


dc_schema = DcSchema()


class OtherlocationsSchema(Schema):
    _FILENAME = "otherlocations"
    _EXTENSION = FileExtension.XLSX
    _SCHEMA_TYPE = SchemaType.MULTI

    ID = "ID"
    X = "x"
    Y = "y"

    def _defined_datatypes(self) -> Dict[str, Dict[str, DataType]]:
        return {
            "customer": {
                OtherlocationsSchema.ID: DataType.STRING,
                OtherlocationsSchema.X: DataType.INTEGER,
                OtherlocationsSchema.Y: DataType.INTEGER,
            },
            "xdock": {
                OtherlocationsSchema.ID: DataType.STRING,
                OtherlocationsSchema.X: DataType.INTEGER,
                OtherlocationsSchema.Y: DataType.INTEGER,
            },
        }


otherlocations_schema = OtherlocationsSchema()


class StoresSchema(Schema):
    _FILENAME = "stores"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = "ID"
    X = "x"
    Y = "y"

    def _defined_datatypes(self) -> Dict[str, DataType]:
        return {
            StoresSchema.ID: DataType.STRING,
            StoresSchema.X: DataType.INTEGER,
            StoresSchema.Y: DataType.INTEGER,
        }


stores_schema = StoresSchema()


all_schemas = [
    dc_schema,
    otherlocations_schema,
    stores_schema,
]
```
:::

```{note}
The fields `_FILENAME`, `_EXTENSION`, and `_SCHEMA_TYPE` are required — an exception is raised at construction if any are missing.
```

```{important}
A single `Schema` corresponds to a single file.
When a file contains more than one data table (e.g., multiple Excel sheets), set `_SCHEMA_TYPE` to `MULTI` and return a nested dictionary from `_defined_datatypes`, as done for `OtherlocationsSchema` above.
The outer-dictionary keys must match the table identifiers (e.g., the sheet names of an xlsx).
```

```{tip}
Defining column names as class variables (e.g., `ID = "ID"`) is not strictly necessary, but it makes the code more readable, prevents typos, and lets your IDE assist with autocompletion — especially when column names are long or appear in many places.
```

## Review the generated ETL factory

Open `src/data_handling/etl_factory.py`. The wizard created a `TSPETLFactory` with extractors already configured for each input file:

:::{dropdown} {octicon}`code` Code
:color: info

```{code-block} python
:caption: `etl_factory.py` (as generated)
:linenos:
from typing import Dict

import algomancy_data as de
from algomancy_data import File
from algomancy_data.extractor import (
    ExtractionSequence,
    CSVSingleExtractor,
    XLSXMultiExtractor,
    XLSXSingleExtractor,
)
from algomancy_data.transformer import TransformationSequence
from algomancy_utils import Logger

from src.data_handling.generated_schemas import all_schemas
from src.data_handling.generated_schemas import dc_schema, otherlocations_schema, stores_schema


class TSPETLFactory(de.SimpleETLFactory):

    @classmethod
    def create_extraction_sequence(
        cls, files=None, schemas=None, logger: Logger = None,
    ) -> ExtractionSequence:
        sequence = ExtractionSequence(logger=logger)

        # Extract dc
        sequence.add_extractor(
            XLSXSingleExtractor(
                file=files["dc"],
                schema=dc_schema,
                sheet_name="Sheet1",
                logger=logger,
            )
        )

        # Extract otherlocations
        sequence.add_extractor(
            XLSXMultiExtractor(
                file=files["otherlocations"],
                schema=otherlocations_schema,
                logger=logger,
            )
        )

        # Extract stores
        sequence.add_extractor(
            CSVSingleExtractor(
                file=files["stores"],
                schema=stores_schema,
                logger=logger,
                separator=",",
            )
        )

        return sequence

    @classmethod
    def create_transformation_sequence(
        cls, schemas=None, logger: Logger = None,
    ) -> TransformationSequence:
        # TODO: Add transformers to process your data.
        return TransformationSequence(logger=logger)

    @classmethod
    def create_validation_sequence(
        cls, schemas, logger: Logger = None,
    ) -> de.ValidationSequence:
        vs = de.ValidationSequence(logger=logger)
        vs.add_validator(de.ExtractionSuccessVerification())
        vs.add_validator(
            de.SchemaValidator(
                schemas=list(schemas.values()),
                severity=de.ValidationSeverity.CRITICAL,
            )
        )
        return vs

    @classmethod
    def create_loader(cls, logger: Logger = None) -> de.Loader:
        # TODO: Customize if you need a custom data container.
        return de.DataSourceLoader(logger)
```
:::

An ETL factory has four responsibilities:

1. **Extract** — read the input files as configured by the schemas.
2. **Validate** — run validations on the extracted data.
3. **Transform** — reshape the extracted DataFrames into the form needed for loading.
4. **Load** — build the application data model from the transformed data.

Extraction and validation are already complete. We now need to replace the placeholder `create_transformation_sequence` and `create_loader` with TSP-specific implementations.

At this point you can verify that extraction works:
1. Run `main.py`.
2. Open the dashboard at `http://127.0.0.1:8050`.
3. Go to the Data page and import the files from `data/setup/`.
4. Verify that all three files are loaded without errors.

## Transform

We transform all input data into a single pandas DataFrame that lists the locations, then derive a routes DataFrame from it.

1. Create the directory `src/data_handling/transformers/`.

2. Create `transform_create_location_df.py` — initialise an empty locations DataFrame:

:::{dropdown} {octicon}`code` Code
:color: info

```python
import pandas as pd
from algomancy_data import Transformer


class TransformCreateLocations(Transformer):
    def __init__(self, location_df_name: str, logger=None) -> None:
        super().__init__(name="Create location df transformer", logger=logger)
        self.location_df_name = location_df_name

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        if data.get(self.location_df_name, None) is None:
            data[self.location_df_name] = pd.DataFrame(columns=['id', 'x', 'y'])
```
:::

3. Create one transformer per input source that appends its rows to the locations DataFrame.
   Each follows the same pattern — rename columns and concatenate:

:::{dropdown} {octicon}`code` Code — customer transformer
:color: info

```python
# transform_customer_to_location.py
import pandas as pd
from algomancy_data import Transformer


class TransformCustomerToLocation(Transformer):
    def __init__(self, location_df_name: str, logger=None) -> None:
        super().__init__(name="Location Transformer", logger=logger)
        self.location_df_name = location_df_name
        self.df_name = 'otherlocations.customer'
        self.column_mapping = {'ID': 'id', 'x': 'x', 'y': 'y'}

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        data_df = data.get(self.df_name, None)
        data_df_locations = data.get(self.location_df_name, None)

        if (data_df is not None) and (data_df_locations is not None):
            normalized = (
                data_df
                .rename(columns=self.column_mapping)
                .reindex(columns=data_df_locations.columns)
                .astype(data_df_locations.dtypes.to_dict())
            )
            data[self.location_df_name] = pd.concat(
                [data_df_locations, normalized], ignore_index=True
            )
```
:::

   Create `TransformXDockToLocation`, `TransformDCToLocation`, and `TransformStoresToLocation` in the same way,
   changing `df_name` to `'otherlocations.xdock'`, `'dc'`, and `'stores'` respectively:

:::{dropdown} {octicon}`code` Code — remaining source transformers
:color: info

```python
# transform_xdock_to_location.py
class TransformXDockToLocation(Transformer):
    def __init__(self, location_df_name: str, logger=None) -> None:
        super().__init__(name="Location Transformer", logger=logger)
        self.location_df_name = location_df_name
        self.df_name = 'otherlocations.xdock'
        self.column_mapping = {'ID': 'id', 'x': 'x', 'y': 'y'}

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        data_df = data.get(self.df_name, None)
        data_df_locations = data.get(self.location_df_name, None)
        if (data_df is not None) and (data_df_locations is not None):
            normalized = (
                data_df.rename(columns=self.column_mapping)
                .reindex(columns=data_df_locations.columns)
                .astype(data_df_locations.dtypes.to_dict())
            )
            data[self.location_df_name] = pd.concat(
                [data_df_locations, normalized], ignore_index=True
            )


# transform_dc_to_location.py
class TransformDCToLocation(Transformer):
    def __init__(self, location_df_name: str, logger=None) -> None:
        super().__init__(name="Location Transformer", logger=logger)
        self.location_df_name = location_df_name
        self.df_name = 'dc'
        self.column_mapping = {'ID': 'id', 'x': 'x', 'y': 'y'}

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        data_df = data.get(self.df_name, None)
        data_df_locations = data.get(self.location_df_name, None)
        if (data_df is not None) and (data_df_locations is not None):
            normalized = (
                data_df.rename(columns=self.column_mapping)
                .reindex(columns=data_df_locations.columns)
                .astype(data_df_locations.dtypes.to_dict())
            )
            data[self.location_df_name] = pd.concat(
                [data_df_locations, normalized], ignore_index=True
            )


# transform_stores_to_location.py
class TransformStoresToLocation(Transformer):
    def __init__(self, location_df_name: str, logger=None) -> None:
        super().__init__(name="Location Transformer", logger=logger)
        self.location_df_name = location_df_name
        self.df_name = 'stores'
        self.column_mapping = {'ID': 'id', 'x': 'x', 'y': 'y'}

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        data_df = data.get(self.df_name, None)
        data_df_locations = data.get(self.location_df_name, None)
        if (data_df is not None) and (data_df_locations is not None):
            normalized = (
                data_df.rename(columns=self.column_mapping)
                .reindex(columns=data_df_locations.columns)
                .astype(data_df_locations.dtypes.to_dict())
            )
            data[self.location_df_name] = pd.concat(
                [data_df_locations, normalized], ignore_index=True
            )
```
:::

4. Create `transform_location_to_routes.py` — derive a routes DataFrame as the Cartesian product of all locations, with Euclidean distance as cost:

:::{dropdown} {octicon}`code` Code
:color: info

```python
import pandas as pd
from algomancy_data import Transformer


class TransformLocationToRoutes(Transformer):
    def __init__(self, location_df_name: str, routes_df_name: str, logger=None) -> None:
        super().__init__(name="Transform location to routes", logger=logger)
        self._location_df_name = location_df_name
        self._routes_df_name = routes_df_name

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        locations = data.get(self._location_df_name, None)

        # Cartesian product with itself
        routes = locations.merge(locations, how='cross', suffixes=('_from', '_to'))
        routes = routes[routes['id_from'] != routes['id_to']]

        routes['distance'] = routes.apply(
            lambda row: (
                (row['x_from'] - row['x_to']) ** 2 + (row['y_from'] - row['y_to']) ** 2
            ) ** 0.5,
            axis=1
        )
        routes['cost'] = routes['distance'] * 1.0

        data[self._routes_df_name] = routes
```
:::

5. Register all transformers in `etl_factory.py` by replacing the placeholder `create_transformation_sequence`:

:::{dropdown} {octicon}`code` Code
:color: info

```python
@classmethod
def create_transformation_sequence(cls, schemas=None, logger=None) -> TransformationSequence:
    sequence = TransformationSequence()
    location_df_name = 'transform_locations'
    routes_df_name = 'transform_routes'
    sequence.add_transformer(TransformCreateLocations(location_df_name=location_df_name, logger=logger))
    sequence.add_transformer(TransformCustomerToLocation(location_df_name=location_df_name, logger=logger))
    sequence.add_transformer(TransformXDockToLocation(location_df_name=location_df_name, logger=logger))
    sequence.add_transformer(TransformStoresToLocation(location_df_name=location_df_name, logger=logger))
    sequence.add_transformer(TransformDCToLocation(location_df_name=location_df_name, logger=logger))
    sequence.add_transformer(TransformLocationToRoutes(
        location_df_name=location_df_name,
        routes_df_name=routes_df_name,
        logger=logger,
    ))
    return sequence
```
:::

6. Run `main.py`, import the data, and verify that `transform_locations` appears as a combined table.

## Load

We build a domain-specific data model from the transformed DataFrames — a network of `Location` and `Route` objects managed by a `NetworkManager`.

Create the directory `src/data_handling/data_model/`.

### Locations

We will use locations in the visualisation part of this tutorial. Create `location.py`:

:::{dropdown} {octicon}`code` Code
:color: info

```python
class Location:
    def __init__(self, id: str, x: float, y: float):
        self._id = id
        self._x = x
        self._y = y

    @property
    def id(self):
        return self._id

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y
```
:::

### Routes

We will use routes in the optimisation part of this tutorial. Create `route.py`:

:::{dropdown} {octicon}`code` Code
:color: info

```python
from data_handling.data_model.location import Location


class Route:
    def __init__(self, from_id: str, to_id: str, cost: float):
        self.route_id = from_id + '_' + to_id
        self._from_id = from_id
        self._to_id = to_id
        self._cost = cost

    @property
    def cost(self):
        return self._cost

    @property
    def from_id(self):
        return self._from_id

    @property
    def to_id(self):
        return self._to_id
```
:::

### Network Manager

Create `network_manager.py` to manage the set of locations and routes:

:::{dropdown} {octicon}`code` Code
:color: info

```python
from typing import List
from src.data_handling.data_model.location import Location
from src.data_handling.data_model.route import Route


class NetworkManager:
    def __init__(self):
        self._locations: dict[str, Location] = {}
        self._routes: dict[tuple[str, str], Route] = {}
        self._reachable_locations_from_location: dict[str, List[Location]] = {}

    def add_location(self, location: Location):
        self._locations[location.id] = location

    def add_route(self, route: Route):
        from_location, to_location = self.get_route_locations(route)
        if from_location is not None and to_location is not None:
            self._routes[(from_location.id, to_location.id)] = route
            if self._reachable_locations_from_location.get(from_location.id, None) is None:
                self._reachable_locations_from_location[from_location.id] = [to_location]
            else:
                self._reachable_locations_from_location[from_location.id] += [to_location]

    def get_locations(self) -> list[Location]:
        return list(self._locations.values())

    def get_location(self, location_id: str) -> Location:
        return self._locations[location_id]

    def get_route_locations(self, route: Route) -> tuple[Location, Location]:
        return self.get_location(route.from_id), self.get_location(route.to_id)

    def get_routes(self) -> list[Route]:
        return list(self._routes.values())

    def get_route(self, from_location_id: str, to_location_id: str) -> Route:
        return self._routes[(from_location_id, to_location_id)]

    def get_reachable_locations(self, location_id: str) -> List[Location]:
        return self._reachable_locations_from_location[location_id]
```
:::

### Data Model

Create `data_model.py` as a `DataSource` subclass so we can attach domain objects to the loaded data:

:::{dropdown} {octicon}`code` Code
:color: info

```python
from datetime import datetime
from typing import List

import pandas as pd
from algomancy_data import DataSource, DataClassification, ValidationMessage
from data_handling.data_model.network_manager import NetworkManager


class DataModel(DataSource):
    def __init__(
            self,
            ds_type: DataClassification,
            name: str = None,
            tables: dict[str, pd.DataFrame] | None = None,
            validation_messages: List[ValidationMessage] = None,
            ds_id: str | None = None,
            creation_datetime: datetime | None = None,
    ):
        super().__init__(
            ds_type=ds_type,
            name=name,
            validation_messages=validation_messages,
            ds_id=ds_id,
            creation_datetime=creation_datetime,
        )

        if tables is not None:
            self.tables = tables

        self._network_manager: NetworkManager | None = None

    def set_network_manager(self, network_manager: NetworkManager):
        self._network_manager = network_manager

    @property
    def network_manager(self):
        return self._network_manager
```
:::

### Loader

Create the directory `src/data_handling/loaders/` and add `loader.py`:

:::{dropdown} {octicon}`code` Code
:color: info

```python
from typing import List
from algomancy_data import Loader, ValidationMessage, DataClassification
import pandas as pd
from data_handling.data_model.data_model import DataModel
from data_handling.data_model.location import Location
from data_handling.data_model.network_manager import NetworkManager
from data_handling.data_model.route import Route


class DataModelLoader(Loader):
    def load(
        self,
        name: str,
        data: dict[str, pd.DataFrame],
        validation_messages: List[ValidationMessage],
        ds_type: DataClassification = DataClassification.MASTER_DATA,
    ) -> DataModel:
        datamodel = DataModel(
            tables=data,
            ds_type=ds_type,
            name=name,
            validation_messages=validation_messages,
        )
        self.load_network_manager(dm=datamodel)
        self.load_locations(dm=datamodel)
        self.load_routes(dm=datamodel)
        return datamodel

    @staticmethod
    def load_network_manager(dm: DataModel):
        dm.set_network_manager(NetworkManager())

    @staticmethod
    def load_locations(dm: DataModel):
        data_locations = dm.get_table("transform_locations")
        nm = dm.network_manager
        for _, row in data_locations.iterrows():
            nm.add_location(Location(id=row["id"], x=row["x"], y=row["y"]))

    @staticmethod
    def load_routes(dm: DataModel):
        data_routes = dm.get_table("transform_routes")
        nm = dm.network_manager
        for _, row in data_routes.iterrows():
            route = Route(from_id=row["id_from"], to_id=row["id_to"], cost=row["cost"])
            from_location, to_location = nm.get_route_locations(route=route)
            if from_location is None or to_location is None:
                continue
            nm.add_route(route=route)
```
:::

Register the loader in `etl_factory.py` by replacing `DataSourceLoader` with `DataModelLoader`:

```python
@classmethod
def create_loader(cls, logger=None) -> Loader:
    return DataModelLoader(logger)
```

Also update `main.py` to use `DataModel` as the data object type:

```python
data_object_type=DataModel,
```

## Next step
All right. The information is loaded in Algomancy. Now it is time to define the {ref}`algorithm(s)<tutorial-algorithms-ref>`.
