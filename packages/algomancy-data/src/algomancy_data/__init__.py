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
from .database import DatabaseDataManager
from .datasource import BaseDataSource, DataSource, DataClassification, BASEDATASOURCE
from .schema import Schema, DataType, FileExtension, SchemaType, Column, ColumnGroup
from .etl import (
    ETLFactory,
    SimpleETLFactory,
    ETLConstructionError,
    ETLPipeline,
    ETLResult,
)
from .extractor import (
    Extractor,
    SingleExtractor,
    MultiExtractor,
    CSVSingleExtractor,
    XLSXSingleExtractor,
    XLSXMultiExtractor,
    JSONSingleExtractor,
    DataFrameExtractor,
)
from .transformer import (
    Transformer,
    NoopTransformer,
    CleanTransformer,
    JoinTransformer,
    OptionalColumnGuard,
    CascadeDropTransformer,
    CascadeSnapshot,
)
from .relations import Relation, resolve_relations_from_schemas, merge_relations
from .validator import (
    Validator,
    DefaultValidator,
    ExtractionSuccessVerification,
    SchemaValidator,
    RequiredColumnsValidator,
    PrimaryKeyValidator,
    UniqueValueValidator,
    MissingValueValidator,
    ForeignKeyValidator,
    ValidationMessage,
    ValidationResult,
    ValidationError,
    ValidationSeverity,
    ValidationSequence,
)
from .loader import Loader, DataSourceLoader
from .file import File, CSVFile, JSONFile, XLSXFile
from .registry import (
    register_extractor,
    get_extractor_class,
    registered_keys,
    _populate_defaults as _populate_registry_defaults,
)

_populate_registry_defaults()

__all__ = [
    "DataManager",
    "StatefulDataManager",
    "StatelessDataManager",
    "DatabaseDataManager",
    "BaseDataSource",
    "DataSource",
    "DataClassification",
    "BASEDATASOURCE",
    "Schema",
    "Column",
    "ColumnGroup",
    "DataType",
    "SchemaType",
    "ETLFactory",
    "SimpleETLFactory",
    "ETLPipeline",
    "ETLResult",
    "ETLConstructionError",
    "Extractor",
    "SingleExtractor",
    "MultiExtractor",
    "CSVSingleExtractor",
    "XLSXSingleExtractor",
    "XLSXMultiExtractor",
    "JSONSingleExtractor",
    "DataFrameExtractor",
    "Transformer",
    "NoopTransformer",
    "CleanTransformer",
    "JoinTransformer",
    "CascadeDropTransformer",
    "CascadeSnapshot",
    "Relation",
    "resolve_relations_from_schemas",
    "merge_relations",
    "Validator",
    "DefaultValidator",
    "ExtractionSuccessVerification",
    "SchemaValidator",
    "RequiredColumnsValidator",
    "OptionalColumnGuard",
    "PrimaryKeyValidator",
    "UniqueValueValidator",
    "MissingValueValidator",
    "ForeignKeyValidator",
    "ValidationMessage",
    "ValidationResult",
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
    "register_extractor",
    "get_extractor_class",
    "registered_keys",
]
