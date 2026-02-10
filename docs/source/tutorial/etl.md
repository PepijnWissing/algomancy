(tutorial-etl-ref)=
# Data intake
An Algomancy app expects to read data by way of an {ref}`ETL<etl-ref>` process.
The steps of this process always follow the same pattern, but we need to configure the app such that the needs of our
project are met. 

We need to write the following steps
1. Declare the configurations of the input files
2. Create the skeleton of our own {ref}`ETL factory<fundamentals-etl-factory-ref>`, which will create a pipeline whenever we wish to run the data intake.  
3. Fill in `create_extraction_sequence(..)`
4. Fill in `create_validation_sequence(..)`
5. Fill in `create_transformation_sequence(..)`
6. Define the {ref}`data container<fundamentals-data-container-ref>` to house our loaded data
7. Fill in `create_loader(..)`


## Define the input files
We start by defining the structure of the input files. This description consists of two parts, 
the first part defines the table structure in each input file and the second part defines 
the file (in terms of file type, file name etc.)
1. Create a file `input_configs.py `in the directory `src/data_handling/`
2. For each table in an input file (could be multiple in an Excel), create a `Schema` subclass in `input_configs.py`. 
This Schema class defines the table structure:
:::{dropdown} {octicon}`code` Code
:color: info

```python
from typing import Dict
from algomancy_data import (Schema,
                            DataType,
                            SingleInputFileConfiguration,
                            FileExtension,
                            MultiInputFileConfiguration)


class DCSchema(Schema):
    ID = "ID"
    X = "x"
    Y = "y"

    @property
    def datatypes(self) -> Dict[str, DataType]:
        return {
            DCSchema.ID: DataType.STRING,
            DCSchema.X: DataType.INTEGER,
            DCSchema.Y: DataType.INTEGER,
        }


class CustomerSchema(Schema):
    ID = "ID"
    X = "x"
    Y = "y"

    @property
    def datatypes(self) -> Dict[str, DataType]:
        return {
            CustomerSchema.ID: DataType.STRING,
            CustomerSchema.X: DataType.INTEGER,
            CustomerSchema.Y: DataType.INTEGER,
        }


class XDockSchema(Schema):
    ID = "ID"
    X = "x"
    Y = "y"

    @property
    def datatypes(self) -> Dict[str, DataType]:
        return {
            XDockSchema.ID: DataType.STRING,
            XDockSchema.X: DataType.INTEGER,
            XDockSchema.Y: DataType.INTEGER,
        }


class StoresSchema(Schema):
    ID = "ID"
    X = "x"
    Y = "y"

    @property
    def datatypes(self) -> Dict[str, DataType]:
        return {
            StoresSchema.ID: DataType.STRING,
            StoresSchema.X: DataType.INTEGER,
            StoresSchema.Y: DataType.INTEGER,
        }
```
:::
3. At the end of input_configs.py, we describe the input file properties (the type of file, file name etc.). 
Add each file configuration the array of input_configs:
:::{dropdown} {octicon}`code` Code
:color: info

```python
input_configs = [
    SingleInputFileConfiguration(
        extension=FileExtension.XLSX,
        file_name="dc",
        file_schema=DCSchema(),
    ),
    MultiInputFileConfiguration(
        extension=FileExtension.XLSX,
        file_name="otherlocations",
        file_schemas={
            "customer": CustomerSchema(),
            "xdock": XDockSchema(),
        },
    ),
    SingleInputFileConfiguration(
        extension=FileExtension.CSV,
        file_name="stores",
        file_schema=StoresSchema(),
    ),
]
```
:::

## ETL Factory
Before we can use the input file configuration that we have just created, 
we need to create an ETLFactory that can extract the input files.

Create a case specific ETLFactory in the directory src/data_handling, i.e., a subclass of ETLFactory.
An ETLFactory is a container class with four different types of main functions
   1. An extract function: extracts the files as configured in input_configs.py.
   2. A validation function: validates the extracted files against user-defined validations.
   3. A transformation function: transforms the extracted files (represented in pandas DataFrames). To 
   other pandas Dataframes that can be used for loading.
   4. A loader function: loads the transformed data into the system.
An example implementation of the TSPETLFactory is given below:
:::{dropdown} {octicon}`code` Code
:color: info

```python
from typing import Dict, TypeVar, cast

from algomancy_data import (
   File,
   CSVFile,
   XLSXFile,
   ETLFactory,
   ValidationSequence,
   ExtractionSuccessVerification,
   SchemaValidator,
   ValidationSeverity,
   Loader,
   DataSourceLoader,
)
from algomancy_data.extractor import (
   ExtractionSequence,
   CSVSingleExtractor,
   XLSXSingleExtractor,
   XLSXMultiExtractor,
)
from algomancy_data.transformer import TransformationSequence, CleanTransformer

F = TypeVar("F", bound=File)


class TSPETLFactory(ETLFactory):
   def __init__(self, configs, logger=None):
      super().__init__(configs, logger)

   def create_extraction_sequence(
           self,
           files: Dict[str, F],  # name to path format
   ) -> ExtractionSequence:
      """
      Input:
          files: A dictionary mapping file names to file paths.

      Output:
          An extraction sequence object

      raises:
          ETLConstructionError: If any of the expected files or configurations are missing.
      """
      sequence = ExtractionSequence()
      return sequence

   def create_validation_sequence(self) -> ValidationSequence:
      vs = ValidationSequence(logger=self.logger)

      vs.add_validator(ExtractionSuccessVerification())

      vs.add_validator(
         SchemaValidator(
            schemas=self.input_configurations,
            severity=ValidationSeverity.CRITICAL,
         )
      )

      return vs

   def create_transformation_sequence(self) -> TransformationSequence:
      sequence = TransformationSequence()
      sequence.add_transformer(CleanTransformer(self.logger))
      return sequence

   def create_loader(self) -> Loader:
      return DataSourceLoader(self.logger)
```
:::

## Extract
1. Add an extractor in the function `create_extraction_sequence` for each file in `input_configs.py.` 
Simply fill the `sequence.add_extractor` function with the appropriate extractor and its arguments:
:::{dropdown} {octicon}`code` Code
:color: info

```python
def create_extraction_sequence(
        self,
        files: Dict[str, F],  # name to path format
) -> ExtractionSequence:
    """
    Input:
        files: A dictionary mapping file names to file paths.

    Output:
        An extraction sequence object

    raises:
        ETLConstructionError: If any of the expected files or configurations are missing.
    """
    sequence = ExtractionSequence()

    sequence.add_extractor(
        CSVSingleExtractor(
            file=cast(CSVFile, files["stores"]),
            schema=self.get_schema("stores"),
            logger=self.logger,
            separator=",",
        )
    )
    sequence.add_extractor(
        XLSXSingleExtractor(
            file=cast(XLSXFile, files["dc"]),
            schema=self.get_schema("dc"),
            sheet_name=0,
            logger=self.logger,
        )
    )
    sequence.add_extractor(
        XLSXMultiExtractor(
            file=cast(XLSXFile, files["otherlocations"]),
            schemas=self.get_schema("otherlocations"),
            logger=self.logger,
        )
    )

    return sequence
```
:::

2. Update main.py such that it uses the `input_configs.py` and the newly created TSPETLFactory:
   1. Import the `input_configs.py` file:
   ```python
   from data_handling.input_configs import input_configs
    ```
   2. Import the TSPETLFactory class:
   ```python
   from data_handling.TSPETLFactory import TSPETLFactory
   ```
   3. Modify the arguments of AppConfiguration to use TSPETLFactory and input_configs
   ```python
   app_cfg = AppConfiguration(
        etl_factory=TSPETLFactory,
        kpi_templates={'placeholder': PlaceholderKPI},
        algo_templates={'placeholder': PlaceholderAlgorithm},
        input_configs=input_configs,
        data_object_type=DataSource,
        autocreate=False, #this will be the default in next release
        autorun=False, #this will be the default in next release
        host=host,
        port=port,
        data_page="standard",#this will be the default in next release
    )
   ```
3. Run main.py in IDE
4. Open dashboard in browser 127.0.0.1
5. Go to Data page and click Import
6. Import all necessary input files from the data dir
7. Verify that all the information is read.

## Transform
We transform all input data into a single pandas dataframe that describes the locations.
:::{warning}
To do: add context to explain why we are taking the steps below
::: 

1. Create the Transformers directory, `src/data_handling/transformers`
2. We start by creating an empty location dataframe with certain column names. 
Create the file `transform_create_location_df.py` in the directory `src/data_handling/transformers` with
the following code:
:::{dropdown} {octicon}`code` Code
:color: info

```python
import pandas as pd
from algomancy_data import Transformer

class TransformCreateLocations(Transformer):
    def __init__(
            self,
            location_df_name: str,
            logger=None
    ) -> None:
        super().__init__(name="Create location df transformer", logger=logger)
        self.location_df_name = location_df_name

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        if self._logger:
            self._logger.log(f"Create location df in transform")

        if data.get(self.location_df_name, None) is None:
            data[self.location_df_name] = pd.DataFrame(
                columns=['id', 'x', 'y']
            )

```
:::
3. Create a transformer to transform the customer data into a location dataframe. 
That is, create a file `transform_customer_to_location.py` in the directory `src/data_handling/transformers` and fill like below:
:::{dropdown} {octicon}`code` Code
:color: info

```python
import pandas as pd
from algomancy_data import Transformer

class TransformCustomerToLocation(Transformer):
    def __init__(
            self,
            location_df_name: str,
            logger=None,
    ) -> None:
        super().__init__(name="Location Transformer", logger=logger)
        self.location_df_name = location_df_name
        self.df_name: str = 'otherlocations.customer'
        self.column_mapping = {
            'ID': 'id',
            'x': 'x',
            'y': 'y',
        }

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        if self._logger:
            self._logger.log(f"Transforming customers to locations")

        data_df = data.get(self.df_name, None)
        data_df_locations = data.get(self.location_df_name,None)

        if (data_df is not None) and (data_df_locations is not None):
            normalized = (
                data_df
                .rename(columns=self.column_mapping)
                .reindex(columns=data_df_locations.columns)
                .astype(data_df_locations.dtypes.to_dict())
            )
            data[self.location_df_name] = pd.concat(
                [data_df_locations, normalized],
                ignore_index=True
            )
```
:::
4. Create a transformer to transform the xdock data into a location dataframe. 
That is, create a file `transform_xdock_to_location.py` in the directory `src/data_handling/transformers` and fill like below:
:::{dropdown} {octicon}`code` Code
:color: info

```python
import pandas as pd
from algomancy_data import Transformer

class TransformXDockToLocation(Transformer):
    def __init__(
            self,
            location_df_name: str,
            logger=None,
    ) -> None:
        super().__init__(name="Location Transformer", logger=logger)
        self.location_df_name = location_df_name
        self.df_name: str = 'otherlocations.xdock'
        self.column_mapping = {
            'ID': 'id',
            'x': 'x',
            'y': 'y',
        }

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        if self._logger:
            self._logger.log(f"Transforming xdock to locations")

        data_df = data.get(self.df_name, None)
        data_df_locations = data.get(self.location_df_name,None)

        if (data_df is not None) and (data_df_locations is not None):
            normalized = (
                data_df
                .rename(columns=self.column_mapping)
                .reindex(columns=data_df_locations.columns)
                .astype(data_df_locations.dtypes.to_dict())
            )
            data[self.location_df_name] = pd.concat(
                [data_df_locations, normalized],
                ignore_index=True
            )
```
:::
5. Create a transformer to transform the dc data into a location dataframe. 
That is, create a file `transform_dc_to_location.py` in the directory `src/data_handling/transformers` and fill like below:
:::{dropdown} {octicon}`code` Code
:color: info

```python
import pandas as pd
from algomancy_data import Transformer

class TransformDCToLocation(Transformer):
    def __init__(
            self,
            location_df_name: str,
            logger=None,
    ) -> None:
        super().__init__(name="Location Transformer", logger=logger)
        self.location_df_name = location_df_name
        self.df_name: str = 'dc'
        self.column_mapping = {
            'ID': 'id',
            'x': 'x',
            'y': 'y',
        }

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        if self._logger:
            self._logger.log(f"Transforming dc to locations")

        data_df = data.get(self.df_name, None)
        data_df_locations = data.get(self.location_df_name,None)

        if (data_df is not None) and (data_df_locations is not None):
            normalized = (
                data_df
                .rename(columns=self.column_mapping)
                .reindex(columns=data_df_locations.columns)
                .astype(data_df_locations.dtypes.to_dict())
            )
            data[self.location_df_name] = pd.concat(
                [data_df_locations, normalized],
                ignore_index=True
            )
```
:::
6. Create a transformer to transform the stores data into a location dataframe. 
That is, create a file `transform_stores_to_location.py` in the directory `src/data_handling/transformers` and fill like below:
:::{dropdown} {octicon}`code` Code
:color: info

```python
import pandas as pd
from algomancy_data import Transformer

class TransformStoresToLocation(Transformer):
    def __init__(
            self,
            location_df_name: str,
            logger=None,
    ) -> None:
        super().__init__(name="Location Transformer", logger=logger)
        self.location_df_name = location_df_name
        self.df_name: str = 'stores'
        self.column_mapping = {
            'ID': 'id',
            'x': 'x',
            'y': 'y',
        }

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        if self._logger:
            self._logger.log(f"Transforming stores to locations")

        data_df = data.get(self.df_name, None)
        data_df_locations = data.get(self.location_df_name,None)

        if (data_df is not None) and (data_df_locations is not None):
            normalized = (
                data_df
                .rename(columns=self.column_mapping)
                .reindex(columns=data_df_locations.columns)
                .astype(data_df_locations.dtypes.to_dict())
            )
            data[self.location_df_name] = pd.concat(
                [data_df_locations, normalized],
                ignore_index=True
            )
```
:::
7. Create a transformer to transform the locations into routes. A route is an edge between two locations.
That is, create a file `transform_location_to_routes.py` in the directory `src/data_handling/transformers` and fill like below
:::{dropdown} {octicon}`code` Code
:color: info

```python
import pandas as pd
from algomancy_data import Transformer

class TransformLocationToRoutes(Transformer):
    def __init__(
            self,
            location_df_name: str,
            routes_df_name: str,
            logger=None,
    ) -> None:
        super().__init__(name="Transform location to routes", logger=logger)
        self._location_df_name = location_df_name
        self._routes_df_name = routes_df_name

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        if self._logger:
            self._logger.log(f"Transforming locations to routes")

        locations = data.get(self._location_df_name,None)

        # Cartesian product with itself
        routes = locations.merge(locations, how='cross', suffixes=('_from', '_to'))

        # Optionally, remove routes where start and end are the same
        routes = routes[routes['id_from'] != routes['id_to']]

        # calculate the euclidean distance between from and to coordinates
        routes['distance'] = routes.apply(lambda row: ((row['x_from'] - row['x_to']) ** 2 + (row['y_from'] - row['y_to']) ** 2) ** 0.5, axis=1)

        # calculate the route cost
        routes['cost'] = routes['distance'] * 1.0

        # register routes on data dict
        data[self._routes_df_name] = routes
```
:::
8. Call the transformers in the ETL Factory (TSPETLFactory.py):
:::{dropdown} {octicon}`code` Code
:color: info

```python
    def create_transformation_sequence(self) -> TransformationSequence:
        sequence = TransformationSequence()
        location_df_name = 'transform_locations'
        routes_df_name = 'transform_routes'
        sequence.add_transformer(TransformCreateLocations(location_df_name=location_df_name, logger=self.logger))
        sequence.add_transformer(TransformCustomerToLocation(location_df_name=location_df_name, logger=self.logger))
        sequence.add_transformer(TransformXDockToLocation(location_df_name=location_df_name, logger=self.logger))
        sequence.add_transformer(TransformStoresToLocation(location_df_name=location_df_name, logger=self.logger))
        sequence.add_transformer(TransformDCToLocation(location_df_name=location_df_name, logger=self.logger))
        sequence.add_transformer(TransformLocationToRoutes(
            location_df_name=location_df_name,
            routes_df_name=routes_df_name,
            logger=self.logger
        ))
        return sequence
```
:::
9. Run main.py in IDE
10. Open dashboard in browser 127.0.0.1
11. Go to Data page and click Import
12. Import all necessary input files from the data dir
13. Verify that all the information is read and that the data is transformed by inspecting transform_locations

## Load
Create a directory data_model under src/data_handling/ such that you get:
```text
root/
|── assets/
├── data/
└── src/
    ├── data_handling/
    │   ├── data_model/
    │   └── transformers/
    ├── pages/
    └── templates/
        ├── kpi/
        └── algorithm/
```
### Locations
We will use locations in the visualization part of this tutorial. Therefore, we create a class Location.

Create a file location.py in the directory src/data_handling/data_model: 
:::{dropdown} {octicon}`code` Code
:color: info

```python
class Location:
    def __init__(
            self,
            id: str,
            x: float,
            y: float,
    ):
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
We will use routes in the optimization part of this tutorial.

Create a file route.py in the directory src/data_handling/data_model:
:::{dropdown} {octicon}`code` Code
:color: info

```python
from data_handling.data_model.location import Location

class Route:
    def __init__(
            self,
            from_id: str,
            to_id: str,
            cost: float,
    ):
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
We create a NetworkManager class in this tutorial to manage the network of locations and routes.
This class offers the following functionalities:
- Add a location to the network
- Add a route to the network
- Get all locations in the network
- Get all routes in the network
- Get all reachable locations from a location

1. Create the file network_manager.py in the directory src/data_handling/data_model.
:::{dropdown} {octicon}`code` Code
:color: info

```python
from typing import List
from data_handling.data_model.location import Location
from data_handling.data_model.route import Route

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

    def get_locations(self):
        return self._locations.values()

    def get_location(self, location_id: str) -> Location:
        return self._locations[location_id]

    def get_route_locations(self, route:Route) -> tuple[Location, Location]:
        return self.get_location(route.from_id), self.get_location(route.to_id)

    def get_routes(self):
        return self._routes.values()

    def get_route(self, from_location_id: str, to_location_id: str):
        return self._routes[(from_location_id, to_location_id)]

    def get_reachable_locations(self, location_id: str) -> List[Location]:
        return self._reachable_locations_from_location[location_id]
```
:::
### Data Model
We create a DataModel class in this tutorial, that is a subclass of DataSource.
We create this subclass because this enables us to save (list of) objects on the object.
This will prove convenient later when we want to run algorithms on the data. 

Note that we maintain the tables field on the class to keep track of the tables that were loaded.

Create a file data_model.py in the directory src/data_handling/data_model.
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
### Load the objects
We use the transformed pandas dataframes to create the objects in this part of the tutorial.
1. Create the directory loaders in src/data_handling/
2. Create the file loader.py in the directory src/data_handling/loaders.

:::{dropdown} {octicon}`code` Code
:color: info

```python
from typing import List
from algomancy_data import Loader, ValidationMessage, DataClassification
from data_handling.data_model.data_model import DataModel
import pandas as pd
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
        if self.logger:
            self.logger.log("Loading data into DataModel")

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
            nm.add_location(
                location = Location(
                    id=row["id"],
                    x=row["x"],
                    y=row["y"],
                )
            )

    @staticmethod
    def load_routes(dm: DataModel):
        data_routes = dm.get_table("transform_routes")
        nm = dm.network_manager
        for _, row in data_routes.iterrows():
            route = Route(
                from_id=row["id_from"],
                to_id=row["id_to"],
                cost=row["cost"],
            )

            from_location, to_location = nm.get_route_locations(route=route)

            if from_location is None or to_location is None:
                continue

            nm.add_route(route=route)
```
:::
3. Register the loader to the ETL Factory (TSPETLFactory.py). That is, replace DataSourceLoad by the newly
created DataModelLoader.
```python
    def create_loader(self) -> Loader:
        return DataModelLoader(self.logger)
```

## Next step
All right. The information is loaded in Algomancy. Now it is time to define the {ref}`algorithm(s)<tutorial-algorithm-ref>`.
