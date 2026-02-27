"""Core data-handling primitives used throughout Algomancy.

This package provides small, composable building blocks to define and run
ETL pipelines and to represent datasets in a consistent way. The main
concepts are:

- DataSource: an in-memory collection of named pandas DataFrames.
- ETLFactory/ETLPipeline: helpers to construct and execute Extract-Transform-Load
  flows from uploaded files using schemas, validators and transformers.
- Extractors/Transformers/Validators/Loader: pluggable steps for ETL.
- DataManager: orchestrates ETL and persistence concerns for one or more
  datasets (stateful or stateless variants).

Public classes are re-exported at the package level for convenience, so you
can import most types via ``from algomancy_data import ...``.
"""

from .datamanager import DataManager, StatelessDataManager, StatefulDataManager
from .datasource import BaseDataSource, DataSource, DataClassification, BASE_DATA_BOUND
from .schema import Schema, DataType, FileExtension, SchemaType
from .etl import ETLFactory, ETLConstructionError, ETLPipeline
from .extractor import (
    Extractor,
    SingleExtractor,
    MultiExtractor,
    CSVSingleExtractor,
    XLSXSingleExtractor,
    XLSXMultiExtractor,
    JSONSingleExtractor,
)
from .transformer import Transformer, NoopTransformer, CleanTransformer, JoinTransformer
from .validator import (
    Validator,
    DefaultValidator,
    ExtractionSuccessVerification,
    SchemaValidator,
    ValidationMessage,
    ValidationError,
    ValidationSeverity,
    ValidationSequence,
)
from .loader import Loader, DataSourceLoader
from .file import File, CSVFile, JSONFile, XLSXFile

__all__ = [
    "DataManager",
    "StatefulDataManager",
    "StatelessDataManager",
    "BaseDataSource",
    "DataSource",
    "DataClassification",
    "BASE_DATA_BOUND",
    "Schema",
    "DataType",
    "SchemaType",
    "ETLFactory",
    "ETLPipeline",
    "ETLConstructionError",
    "Extractor",
    "SingleExtractor",
    "MultiExtractor",
    "CSVSingleExtractor",
    "XLSXSingleExtractor",
    "XLSXMultiExtractor",
    "JSONSingleExtractor",
    "Transformer",
    "NoopTransformer",
    "CleanTransformer",
    "JoinTransformer",
    "Validator",
    "DefaultValidator",
    "ExtractionSuccessVerification",
    "SchemaValidator",
    "ValidationMessage",
    "ValidationError",
    "ValidationSeverity",
    "ValidationSequence",
    "Loader",
    "DataSourceLoader",
    "FileExtension",
    "File",
    "JSONFile",
    "CSVFile",
    "XLSXFile",
]
