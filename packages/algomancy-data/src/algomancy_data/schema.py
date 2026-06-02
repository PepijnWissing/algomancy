"""Schema primitives for defining structured tabular data.

This module provides a ``Schema`` abstraction that declares columns via
``Column`` instances as class attributes.  The legacy ``_DATATYPES`` dict is
still accepted but emits a ``DeprecationWarning``; migrate to ``Column``
declarations to silence it.
"""

import inspect
import warnings
from abc import ABC
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Dict, List, Tuple, Type


class DataType(StrEnum):
    """Enumeration of supported logical data types for schema fields."""

    STRING = "string"
    DATETIME = "datetime64[ns]"
    INTEGER = "int64"
    FLOAT = "float64"
    BOOLEAN = "boolean"
    CATEGORICAL = "categorical"
    INTERVAL = "interval"


class FileExtension(StrEnum):
    """Supported file extensions for input files."""

    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"


class SchemaType(StrEnum):
    """Enumeration of supported schema types."""

    SINGLE = "single"
    MULTI = "multi"


@dataclass
class Column:
    """Metadata for a single schema column.

    Args:
        name: Actual column name as it appears in the source data.
        dtype: The expected ``DataType`` of this column.
        optional: If ``True`` the column may be absent in the source data.
        primary_key: If ``True`` this column is part of the (joint) primary key.
        default: Value used when the column is absent and ``optional=True``.
        nullable: If ``True`` the column may contain null/NaN values.
        unique: If ``True`` all values in the column must be distinct.
        description: Human-readable description of the column.
        foreign_key: Optional ``(parent_table, parent_column)`` tuple declaring
            that this column references a column on another table. Used by
            :class:`ForeignKeyValidator` (for reporting violations) and by
            :class:`CascadeDropTransformer` (for cascade cleanup).
        parent_requires_child: If ``True``, the referenced parent row requires
            at least one referencing child on this relation; parents with zero
            children get dropped by ``CascadeDropTransformer``. Only meaningful
            when ``foreign_key`` is set.
        track_partial_loss: If ``True``, enables partial-loss cascade for this
            relation: parents that lose *some* (but not all) of their children
            mid-pipeline are dropped. Requires a ``CascadeSnapshot`` paired
            with the cascade transformer. Only meaningful when ``foreign_key``
            is set.
    """

    name: str
    dtype: DataType
    optional: bool = False
    primary_key: bool = False
    default: Any = None
    nullable: bool = False
    unique: bool = False
    description: str = field(default="")
    foreign_key: Tuple[str, str] | None = None
    parent_requires_child: bool = False
    track_partial_loss: bool = False

    def __post_init__(self) -> None:
        if self.foreign_key is None:
            if self.parent_requires_child:
                raise ValueError(
                    f"Column '{self.name}': parent_requires_child=True requires "
                    "foreign_key to be set."
                )
            if self.track_partial_loss:
                raise ValueError(
                    f"Column '{self.name}': track_partial_loss=True requires "
                    "foreign_key to be set."
                )


@dataclass
class ColumnGroup:
    """Metadata for one sheet (sub-schema) of a MULTI schema.

    Declare ``ColumnGroup`` instances as class attributes on a ``Schema``
    subclass with ``_SCHEMA_TYPE = SchemaType.MULTI``::

        class LocationSchema(Schema):
            _FILENAME = "multisheet"
            _EXTENSION = FileExtension.XLSX
            _SCHEMA_TYPE = SchemaType.MULTI

            STEDEN = ColumnGroup("Steden", [
                Column("Country", dtype=DataType.STRING),
                Column("City",    dtype=DataType.STRING),
            ])
            KLANTEN = ColumnGroup("Klanten", [
                Column("ID",   dtype=DataType.INTEGER, primary_key=True),
                Column("Naam", dtype=DataType.STRING),
            ])

    Args:
        name:    Actual sheet / sub-schema name as it appears in the source
                 file (may contain spaces and mixed case).
        columns: Ordered list of ``Column`` objects for this sub-schema.
        source_path: For nested sources (e.g. JSON), the path of keys from
            the root record to the list of dicts that populates this group.
            ``()`` (the default) means the group is built from the root
            record itself; a tuple like ``("PickOrderLines",)`` means each
            root record has a nested list at that key whose elements form
            the rows of this group. Ignored by extractors that do not
            support nesting (e.g. ``XLSXMultiExtractor``).
    """

    name: str
    columns: List[Column]
    source_path: Tuple[str, ...] = field(default_factory=tuple)


class Schema(ABC):
    """Abstract base class for table schemas.

    Declare columns as class attributes using ``Column`` instances::

        class MySchema(Schema):
            _FILENAME = "my_file"
            _EXTENSION = FileExtension.CSV
            _SCHEMA_TYPE = SchemaType.SINGLE

            ID = Column("id", dtype=DataType.STRING, primary_key=True)
            NAME = Column("name", dtype=DataType.STRING)
            VALUE = Column("value", dtype=DataType.FLOAT, optional=True)

    The legacy ``_DATATYPES`` dict is still supported but deprecated.
    """

    _FILENAME: str = "default_filename"
    _EXTENSION: FileExtension | str = "default_extension"
    _SCHEMA_TYPE: SchemaType | str = "default_schema_type"
    _DATATYPES: Dict[str, DataType] | Dict[str, Dict[str, DataType]] | str = (
        "default_datatypes"
    )

    # ------------------------------------------------------------------ #
    # Identity
    # ------------------------------------------------------------------ #

    @classmethod
    def file_name(cls) -> str:
        """Return the base file name (without extension)."""
        if cls._FILENAME == "default_filename":
            raise NotImplementedError("_FILENAME must be overridden by subclasses")
        return cls._FILENAME

    @classmethod
    def extension(cls) -> FileExtension:
        """Return the file extension.

        Accepts any ``StrEnum``-derived value (including user-defined
        ``FileExtension`` subclasses created for custom file formats —
        see :ref:`extending-ref`). A plain ``str`` is upcast to the
        built-in ``FileExtension`` for compatibility, or returned as-is
        when it does not match a built-in value.
        """
        if cls._EXTENSION == "default_extension":
            raise NotImplementedError("_EXTENSION must be overridden by subclasses")
        if isinstance(cls._EXTENSION, FileExtension):
            return cls._EXTENSION
        if isinstance(cls._EXTENSION, StrEnum):
            # Custom extension StrEnum from a user project — pass through.
            return cls._EXTENSION
        if isinstance(cls._EXTENSION, str):
            try:
                return FileExtension(cls._EXTENSION)
            except ValueError:
                # Unknown string extension — return raw so registry lookups
                # can still resolve by string equality.
                return cls._EXTENSION
        raise TypeError(f"Invalid extension type: {type(cls._EXTENSION)}")

    @classmethod
    def schema_type(cls) -> SchemaType:
        """Return the schema type (SINGLE or MULTI)."""
        if cls._SCHEMA_TYPE == "default_schema_type":
            raise NotImplementedError("_SCHEMA_TYPE must be overridden by subclasses")
        if isinstance(cls._SCHEMA_TYPE, SchemaType):
            return cls._SCHEMA_TYPE
        if isinstance(cls._SCHEMA_TYPE, str):
            return SchemaType(cls._SCHEMA_TYPE)
        raise TypeError(f"Invalid schema type: {type(cls._SCHEMA_TYPE)}")

    @classmethod
    def file_name_with_extension(cls) -> str:
        """Return ``<file_name>.<extension>``."""
        return cls._FILENAME + "." + cls._EXTENSION

    # ------------------------------------------------------------------ #
    # Column accessors (new API — issues #73–75)
    # ------------------------------------------------------------------ #

    @classmethod
    def columns(cls) -> Dict[str, Column]:
        """Return an ordered mapping of column name → ``Column``.

        For schemas that declare ``Column`` class attributes the mapping is
        built from those attributes (in class-definition order).

        For schemas that still use the legacy ``_DATATYPES`` dict a
        ``DeprecationWarning`` is emitted and ``Column`` objects are built
        automatically with ``optional=False``, ``primary_key=False``, and
        ``default=None``.

        Raises:
            NotImplementedError: If neither Column attributes nor ``_DATATYPES``
                are defined.
            TypeError: If called on a MULTI schema (use ``datatype_groups()``).
        """

        if not cls.is_single():
            raise TypeError(
                f"{cls.__name__} is a MULTI schema. "
                "Use datatype_groups() to inspect its column groups."
            )

        col_attrs = [attr for attr in vars(cls).values() if isinstance(attr, Column)]
        if col_attrs:
            return {col.name: col for col in col_attrs}

        return cls.get_legacy_columns_with_warning()

    @classmethod
    def get_legacy_columns_with_warning(cls) -> dict[str, Column]:
        if cls._DATATYPES == "default_datatypes":
            raise NotImplementedError(
                f"{cls.__name__} must declare Column attributes or override _DATATYPES"
            )

        warnings.warn(
            f"{cls.__name__} uses the legacy _DATATYPES dict. "
            "Declare Column instances as class attributes instead "
            "(e.g. ID = Column('id', dtype=DataType.STRING)).",
            DeprecationWarning,
            stacklevel=2,
        )
        legacy_columns = {
            col_name: Column(name=col_name, dtype=dtype)
            for col_name, dtype in cls._DATATYPES.items()
        }
        return legacy_columns

    @classmethod
    def column_groups(cls) -> Dict[str, Dict[str, Column]]:
        """Return ``{group_name: {col_name: Column}}`` for MULTI schemas.

        Scans ``vars(cls)`` for ``ColumnGroup`` attributes first (new API).
        Falls back to ``_DATATYPES`` for legacy schemas, emitting a
        ``DeprecationWarning`` and constructing bare ``Column`` objects
        (``optional=False``, ``primary_key=False``, ``default=None``).

        Raises:
            ValueError:          If called on a SINGLE schema.
            NotImplementedError: If neither ColumnGroup attrs nor ``_DATATYPES``
                                 are defined.
        """
        if not cls.is_multi():
            raise ValueError(
                "column_groups() is only available for MULTI schemas. "
                "Use columns() for SINGLE schemas."
            )

        group_attrs = [
            attr for attr in vars(cls).values() if isinstance(attr, ColumnGroup)
        ]
        if group_attrs:
            return {
                grp.name: {col.name: col for col in grp.columns} for grp in group_attrs
            }

        if cls._DATATYPES == "default_datatypes":
            raise NotImplementedError(
                f"{cls.__name__} must declare ColumnGroup attributes or override _DATATYPES"
            )

        warnings.warn(
            f"{cls.__name__} uses the legacy _DATATYPES dict for a MULTI schema. "
            "Declare ColumnGroup instances as class attributes instead "
            "(e.g. STEDEN = ColumnGroup('Steden', [Column('Country', dtype=DataType.STRING)])).",
            DeprecationWarning,
            stacklevel=2,
        )
        return {
            group_name: {
                col_name: Column(name=col_name, dtype=dtype)
                for col_name, dtype in sub_dict.items()
            }
            for group_name, sub_dict in cls._DATATYPES.items()
        }

    @classmethod
    def required_columns(cls) -> List[str]:
        """Return names of non-optional columns."""
        return [name for name, col in cls.columns().items() if not col.optional]

    @classmethod
    def optional_columns(cls) -> List[str]:
        """Return names of optional columns."""
        return [name for name, col in cls.columns().items() if col.optional]

    @classmethod
    def primary_key(cls) -> Tuple[str, ...]:
        """Return tuple of column names that form the (joint) primary key."""
        return tuple(name for name, col in cls.columns().items() if col.primary_key)

    # ------------------------------------------------------------------ #
    # Legacy dtype accessors (kept for internal ETL compatibility)
    # ------------------------------------------------------------------ #

    @classmethod
    def datatypes(cls) -> Dict[str, DataType]:
        """Return ``{column_name: DataType}`` for SINGLE schemas.

        Derived from ``Column`` attributes when present; falls back to the
        legacy ``_DATATYPES`` dict otherwise.

        Raises:
            ValueError: If called on a MULTI schema (use ``datatype_groups()``).
        """
        if not cls.is_single():
            raise ValueError(
                "datatypes() is only available for SINGLE schemas. "
                "Use datatype_groups() for MULTI schemas."
            )

        col_attrs = [attr for attr in vars(cls).values() if isinstance(attr, Column)]
        if col_attrs:
            return {col.name: col.dtype for col in col_attrs}

        if cls._DATATYPES == "default_datatypes":
            raise NotImplementedError("_DATATYPES or Column attributes must be defined")

        return cls._DATATYPES

    @classmethod
    def _validate_datatypes(cls, dtypes: Dict[str, DataType]) -> None:
        for col_name, dtype in dtypes.items():
            assert isinstance(col_name, str), (
                f"Field name must be a string, got {type(col_name)}"
            )
            assert isinstance(dtype, DataType), (
                f"Datatype for field '{col_name}' must be a DataType, got {type(dtype)}"
            )

    @classmethod
    def datatype_groups(cls) -> Dict[str, Dict[str, DataType]]:
        """Return ``{sub_name: {column_name: DataType}}`` for MULTI schemas.

        Derived from ``ColumnGroup`` class attributes when present; falls back
        to the legacy ``_DATATYPES`` nested dict otherwise.

        Raises:
            ValueError:          If called on a SINGLE schema.
            NotImplementedError: If neither ColumnGroup attrs nor ``_DATATYPES``
                                 are defined.
        """
        if not cls.is_multi():
            raise ValueError("datatype_groups() is only available for MULTI schemas")

        group_attrs = [
            attr for attr in vars(cls).values() if isinstance(attr, ColumnGroup)
        ]
        if group_attrs:
            return {
                grp.name: {col.name: col.dtype for col in grp.columns}
                for grp in group_attrs
            }

        if cls._DATATYPES == "default_datatypes":
            raise NotImplementedError("_DATATYPES must be overridden by subclasses")

        dtypes = cls._DATATYPES
        for schema_name, schema_datatypes in dtypes.items():
            assert isinstance(schema_name, str), (
                f"Schema name must be a string, got {type(schema_name)}"
            )
            cls._validate_datatypes(schema_datatypes)

        return dtypes

    @classmethod
    def sub_names(cls) -> List[str]:
        """Return sub-schema names for MULTI schemas."""
        if cls.schema_type() == SchemaType.SINGLE:
            raise ValueError("Single-schema types do not have sub-schemas")
        if cls.schema_type() == SchemaType.MULTI:
            return list(cls.datatype_groups().keys())
        raise ValueError("Invalid schema type")

    # ------------------------------------------------------------------ #
    # Type checks
    # ------------------------------------------------------------------ #

    @classmethod
    def is_multi(cls) -> bool:
        """Return ``True`` if this is a MULTI schema."""
        return cls.schema_type() == SchemaType.MULTI

    @classmethod
    def is_single(cls) -> bool:
        """Return ``True`` if this is a SINGLE schema."""
        return cls.schema_type() == SchemaType.SINGLE

    # ------------------------------------------------------------------ #
    # Sub-schema access
    # ------------------------------------------------------------------ #

    @classmethod
    def get_subschema(cls, key: str) -> Type["Schema"]:
        """Return a synthetic SINGLE schema class for one sheet of a MULTI schema.

        The returned class behaves as a normal ``Schema`` subclass and exposes
        ``datatypes()`` for the requested sub-name.

        Args:
            key: Sub-schema name (e.g. sheet name in an XLSX file).

        Raises:
            ValueError: If called on a SINGLE schema or if ``key`` is invalid.
        """
        if not cls.is_multi():
            raise ValueError("get_subschema() is only available for MULTI schemas")

        if key not in cls.sub_names():
            raise ValueError(
                f"Key '{key}' does not define a subschema. Available: {cls.sub_names()}"
            )

        group_attrs = [
            attr for attr in vars(cls).values() if isinstance(attr, ColumnGroup)
        ]
        if group_attrs:
            matching = next(grp for grp in group_attrs if grp.name == key)
            ns: Dict[str, Any] = {
                "_FILENAME": cls._FILENAME,
                "_EXTENSION": cls._EXTENSION,
                "_SCHEMA_TYPE": SchemaType.SINGLE,
            }
            for col in matching.columns:
                safe_key = "_SYNTH_" + col.name.upper().replace(" ", "_").replace(
                    ".", "_"
                )
                ns[safe_key] = col
            return type(f"{cls.__name__}_{key}", (Schema,), ns)

        sub_datatypes = cls.datatype_groups()[key]
        return type(
            f"{cls.__name__}_{key}",
            (Schema,),
            {
                "_FILENAME": cls._FILENAME,
                "_EXTENSION": cls._EXTENSION,
                "_SCHEMA_TYPE": SchemaType.SINGLE,
                "_DATATYPES": sub_datatypes,
            },
        )

    # ------------------------------------------------------------------ #
    # Validation / introspection helpers
    # ------------------------------------------------------------------ #

    @classmethod
    def validate(cls) -> None:
        """Validate that every declared field name appears in the column mapping.

        Raises:
            AssertionError: If a field name is missing from the column mapping.
        """
        col_names = set(cls.columns().keys())
        for field_name in cls.get_data_members():
            assert field_name in col_names, (
                f"Field '{field_name}' has no corresponding Column definition"
            )

    @classmethod
    def get_data_members(cls) -> List[str]:
        """Return string-valued class attributes that represent column aliases.

        Excludes dunder names, methods, classes, built-ins, descriptors, and
        ``Column`` instances (which are the new-style declaration).
        """
        return [
            name
            for name, attr in vars(cls).items()
            if not (name.startswith("__") and name.endswith("__"))
            and not isinstance(attr, (Column, ColumnGroup))
            and not inspect.isroutine(attr)
            and not inspect.isclass(attr)
            and not inspect.isbuiltin(attr)
            and not inspect.isdatadescriptor(attr)
            and not name.startswith("_")
        ]
