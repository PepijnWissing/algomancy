(etl-ref)=
# Extract, Transform, Load

The ETL engine orchestrates the movement of data from source files into a `DataSource`.
It uses **Sequences** to manage multiple steps of extraction, validation, and transformation.

## ETL Pipeline Components
1. **`ETLFactory`**: Manages the orchestration of ETL processes.
2. **`Schema`**: Contains source file metadata and data types.
1. **`ExtractionSequence`**: Manages a collection of extractors that read files.
2. **`ValidationSequence`**: Runs a series of checks against the raw data.
3. **`TransformationSequence`**: Applies business logic to convert raw data into the final format.
4. **`Loader`**: Handles the final instantiation of the `DataSource`.

## ETL Factory
Any Algomancy project will require an `ETLFactory` to function. 
Simply put, it will generate a data extraction pipeline whenever a set of files needs to be read. 
Typically, this happens either on launch of the application and whenever the end-user uses the _Import_ usecase. 

To implement ETL for a project, you subclass `ETLFactory` and implement the sequence creation methods.
The related components are discussed, below. 

:::{dropdown} {octicon}`eye` Example: ETLFactory
:color: success
TODO Explain example 
```{code-block} python
:caption: Creating an ETLFactory
:linenos: 
from algomancy_data import (ETLFactory, 
                            ExtractionSequence, 
                            CSVExtractor, 
                            TransformationSequence,
                            File)

class MyProjectETLFactory(ETLFactory):
    def create_extraction_sequence(self, files: dict[str, File]):
        sequence = ExtractionSequence()
        
        order_schema = self.get_schema("orders_2026")
        sequence.add_extractor(CSVExtractor(files["orders_2026"], order_schema))
        
        # Add more extractors...
        
        return sequence

    def create_transformation_sequence(self):
        sequence = TransformationSequence()
        
        # Add your custom Transformer objects here...
        
        return sequence
    
    # Implement create_validation_sequence and create_loader...
```
:::

(fundamentals-schema-ref)=
## Schemas
```{note}
As of version 0.4.0, all file configuration is embedded directly within the `Schema` subclass. The separate `InputFileConfiguration` class has been retired.
```
The `Schema` class is the single source of truth for file metadata and data types. 
It combines column definitions with file-level information like filenames and extensions.
A `Schema` must be created for each file that needs to be processed. 

To implement a `Schema`, you should subclass the `Schema` class and define the following attributes:

- `_FILENAME`: The name of the file without the extension.
- `_EXTENSION`: The file extension (e.g., `FileExtension.CSV`, `FileExtension.JSON`).
- `_SCHEMA_TYPE`: The type of schema (e.g., `SchemaType.SINGLE`, `SchemaType.MULTI`).
- `_defined_datatypes()`: A method to define the data types for each column. 

    ```{warning} 
    `_defined_datatypes()` will be replaced by a `_DATATYPES` attribute in v0.5.0]
    ```



:::{dropdown} {octicon}`eye` Example: Schema
:color: success
TODO Explain example 
```{code-block} python
:caption: Creating a Schema
:linenos: 
from algomancy_data import Schema, FileExtension, DataType
from algomancy_data.schema import SchemaType

class OrdersSchema(Schema):
    # File metadata
    _FILENAME = "orders_2026"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    # Column definitions
    ORDER_ID = "id"
    QUANTITY = "qty"
    DATE = "order_date"

    def _defined_datatypes(self):
        return {
            self.ORDER_ID: DataType.STRING,
            self.QUANTITY: DataType.INTEGER,
            self.DATE: DataType.TIME,
        }
```
:::
## Extractors

`Extractors` are responsible for reading data from external files (e.g., CSV, XLSX, JSON) and converting them into 
pandas `DataFrame`s. They also handle the initial data type conversion based on the provided `Schema`.

The `ExtractionSequence` orchestrates one or more `Extractor`s. When the ETL pipeline runs, it calls 
`ExtractionSequence.data`, which triggers the extraction process for all registered extractors and aggregates the 
results into a single dictionary of `DataFrame`s.

The `Extractor` is an abstract base class and can be subclassed to extract custom data formats, if necessary. 
It comes in two flavours:
- `SingleExtractor`: assumes that the data file contains a single table or sheet. 
- `MultiExtractor`: is used when the data source contains multiple tables or sheets, and the schema defines how to 
    map these to individual `DataFrame`s.

The framework provides several concrete implementations for common file types, which should suffice for most use cases.

| Extractor             | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| `CSVSingleExtractor`  | Extracts a single table from a CSV file.                                    |
| `JSONSingleExtractor` | Extracts a single table from a JSON file.                                   |
| `XLSXSingleExtractor` | Extracts a single sheet from an XLSX file.                                  |
| `XLSXMultiExtractor`  | Extracts multiple sheets from an XLSX file (based on a multi-sheet schema). |

### Using extractors

Extractors are typically initialized within the `create_extraction_sequence()` method of your `ETLFactory`. 
You receive a dictionary of `File` objects (keyed by their logical name) and use them to create the appropriate extractors.

Consider the following example:

:::{dropdown} {octicon}`eye` Example: creating an extraction sequence
:color: success
TODO Explain example 
```python
from algomancy_data import ETLFactory, ExtractionSequence, CSVSingleExtractor, XLSXMultiExtractor
from typing import Dict
from algomancy_data.file import File

class MyETLFactory(ETLFactory):
    def create_extraction_sequence(self, files: Dict[str, File]) -> ExtractionSequence:
        sequence = ExtractionSequence(logger=self.logger)
        
        # Add a single CSV extractor
        # 'orders' matches the _FILENAME in OrdersSchema
        sequence.add_extractor(CSVSingleExtractor(
            file=files["orders"],
            schema=self.get_schema("orders"),
            separator=","
        ))
        
        # Add a multi-sheet XLSX extractor
        sequence.add_extractor(XLSXMultiExtractor(
            file=files["inventory"],
            schema=self.get_schema("inventory")
        ))
        
        return sequence
```
:::

## Validators

The `Validators` aim to check the integrity of the raw data. Each `Validator` should be responsible for checking a single 
aspect of the data. The `Validator` class has a single exposed method, `validate()`, which takes a dictionary of
`DataFrame`s as input. The `validate()` method should return a list of `ValidationMessage`s, which are used to document 
any errors that occur during validation.

`Validators` work with a message-based system that allows the entire validation process to be run before reporting. 
This system is based on the `ValidationMessage` class, which has two main attributes: `severity` and `message`. 
`CRITICAL` messages will stop the ETL process; other messages (`INFO`, `WARNING`, and `ERROR`) mostly serve as 
informational messages, and are styled differently in the logging section of the dashboard. 

```{important} 
If any message whose `severity` is `CRITICAL` is raised during validation, the ETL process is terminated after validation.
```

`ValidationSequence` is simply a wrapper that executes a list of `Validator`s and compiles the results. 

### Using validators
The user will typically need to implement their own validators, as most data validation requires a decent bit of context. 
When the `Validators` have been created, the implementation of `create_validation_sequence()` is, once again, fairly straightforward. 
The user simply needs to create an instance of the desired `ValidationSequence`, and add the desired `Validator`s to by 
calling the `add_validator()` method. Consider the following example implementation.

:::{dropdown} {octicon}`eye` Example: ValidationSequence
:color: success
TODO Explain example 
```python

from src import algomancy as de
from typing import Dict, List


# Create an ETLFactory
class MyETLFactory(de.ETLFactory):
    ...

    def create_validation_sequence(self) -> de.ValidationSequence:
        vs = de.ValidationSequence(logger=self.logger)

        vs.add_validator(de.ExtractionSuccessVerification())

        return vs
```
:::

### Creating a validator
To create a custom validator, the user needs to create a class that inherits from `Validator`. The class should primarily
implement the `validate()` method, which is used to validate the data. Consider the following example implementation.

:::{dropdown} {octicon}`eye` Example: validator
:color: success
The below example is a basic validator, which simply checks that each dataframe is not empty; the actual implementation 
depends mostly on the extracted data, in context.
```python
import pandas as pd

from algomancy_data import (Validator, 
                            ValidationSeverity, 
                            ValidationMessage)
from typing import Dict, List

class ExtractionSuccessVerification(Validator):
    """ Checks that the extraction of each single dataframe was successful. """
    def __init__(self) -> None:
        super().__init__()
    
    def validate(self, data: Dict[str, pd.DataFrame]) -> List[ValidationMessage]:
        """ The necessary validation logic. """
        
        # check that each dataframe is not empty
        for name, df in data.items():
            if df.empty:
                self.buffer_message(
                  ValidationSeverity.CRITICAL, 
                  f"Extraction of {name} returned empty DataFrame."
                )
                
        # flush the buffer and return the messages
        self.flush_buffer(success_message="All dataframes were extracted successfully.")
        return self.messages
```
An important point to note: the user can either use the `add_message()` or `buffer_message()` methods to add messages 
to the list of messages. The `flush_buffer()` method is used to add all of the messages in the buffered list to the 
persistent list. If the buffered list was empty, add `success_message` to the persistent list instead. This is a 
practical way to ensure that the `ValidationSequence` always returns a list of messages upon completion, for progress 
tracking. 
:::


## Transformers
> _DeprecatedWarning: At some point, this will be moved to a TransformerSequence._ 

Transformers are a critical component of the ETL process, responsible for cleaning, normalizing, and reshaping raw data into a consistent and usable structure. Each `Transformer` operates on a dictionary of input `DataFrame`s, performing its transformation in-place or creating new tables as needed.

The base `Transformer` class requires only the implementation of a single method:

| Attribute / Method      | Type / Signature                             | Description                                                                        |
|-------------------------|----------------------------------------------|------------------------------------------------------------------------------------|
| `transform()`           | `data: Dict[str, pd.DataFrame] -> dict[...]` | Transforms the data in the provided dictionary. Must be implemented by subclasses. |
| `name`                  | `str`                                        | Human-readable name for the transformer.                                           |

Most transformers *mutate* the input dictionary in-place. By convention, they should document what tables are expected before and after the operation.

### Common Transformers

Several ready-to-use, prebuilt transformers are provided:
- **NoopTransformer**: Passes data through unchanged. Useful for debugging or pipeline scaffolding.
- **CleanTransformer**: Drops rows with missing values and lowercases/strips all column names.
- **JoinTransformer**: Merges/join two tables on a given column and adds the result under a new table name.

Example: creating a transformation sequence in the factory:
:::{dropdown} {octicon}`eye` Example: transformation sequence usage
:color: success

The `ETLFactory` requires the implementation of `create_transformation_sequence()`, which returns a `TransformationSequence` containing all the transformers to be applied.

```{code-block} python
:caption: Implementation of create_transformation_sequence
:linenos:
from algomancy_data import ETLFactory, TransformationSequence, CleanTransformer
from typing import Dict, List


# Create an ETLFactory
class MyETLFactory(ETLFactory):
    ...

    def create_transformation_sequence(self) -> TransformationSequence:
        """ Create and return a TransformationSequence. """
        ts = TransformationSequence(logger=self.logger)

        ts.add_transformer(CleanTransformer(logger=self.logger))

        return ts
```
:::

### Creating a transformer
To create a custom transformer, the user needs to create a class that inherits from `Transformer`. The class should primarily
implement the `transform()` method, which is used to transform the data. Consider the following example implementation.

:::{dropdown} {octicon}`eye` Example: transformer
:color: success
TODO Explain example 
```{code-block} python
:caption: The CleanTransformer
:linenos: 
import pandas as pd
from algomancy_data import Transformer

class CleanTransformer(Transformer):
    def __init__(self, logger=None) -> None:
        super().__init__(name="CleanTransformer", logger=logger)

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        """ the necessary transformation logic."""
        if self.logger:
            self.logger.log("Cleaning dataframes (dropna, lowercase columns)")
        for name, df in data.items():
            df = df.dropna()
            df.columns = [c.lower().strip() for c in df.columns]
```
:::

## Loader

The Loader is responsible for the final step of the ETL process: persisting or handing off the transformed data to its 
destination format, which is a `DataSource` or a class derived from `BaseDataSource`. This means combining the (possibly 
multiple) DataFrames to create some number of persistent object, to be stored in the `DataSource` model.

The `Loader` is called at the very end of the ETL pipeline, after validation and transformation are complete.

### Loader Usage

The framework provides a basic data loader as `DataSourceLoader`, which simply combines all DataFrames into a standard `DataSource` instance.
A custom loader is necessary when the implementation intends to use a Custom Data Source. 

Again, the implementation of `create_loader()` is straightforward; the main task is to create an instance of the desired `Loader`.
Consider the following example implementation

:::{dropdown} {octicon}`eye` Example: Loader usage
:color: success
The below simply creates an instance of the `MyCustomSourceLoader` class, which is a subclass of `Loader`, and could be 
implemented as follows.
```{code-block} python
:caption: Create Loader implementation
:linenos:
from algomancy_data import ETLFactory, Loader 
from typing import Dict, List


class MyETLFactory(ETLFactory):
    ...

    def create_loader(self) -> Loader:
        return MyCustomSourceLoader(self.logger)
```
:::

### Creating a Loader
TODO Text here
:::{dropdown} {octicon}`eye` Example: Loader
:color: success
TODO Explain example 
```python

from src import algomancy as de
import pandas as pd
from algomancy.dashboardlogger import Logger
from typing import Dict, List


# suppose that the MyCustomSource example, from the DataSource section, is imported here

# suppose, moreover, that the ETL pipeline up to this point has yielded a pair of DataFrames, customers and suppliers, 
#    which both describe locations in the obvious way.

class MyCustomSourceLoader(de.Loader):
    def __init__(self, logger: Logger) -> None:
        super().__init__(logger=logger)

    def load(
            self, name: str, data: Dict[str, pd.DataFrame], messages: List[de.ValidationMessage],
            ds_type: de.DataClassification
    ) -> MyCustomSource:
        """ Combines the transformed data into a DataSource. """
        customers = data['customers']
        suppliers = data['suppliers']

        locations = {}
        for customer in customers.iterrows():
            locations[customer['name']] = Location(name=customer['name'], type="customer",
                                                   longitude=customer['longitude'],
                                                   latitude=customer['latitude'])

        for supplier in suppliers.iterrows():
            locations[supplier['id']] = Location(name=supplier['id'], type="supplier", longitude=supplier['lat'],
                                                 latitude=supplier['lon'])

        return MyCustomSource(ds_type=de.DataClassification.MASTER_DATA, name="example", locations=locations)
```
:::