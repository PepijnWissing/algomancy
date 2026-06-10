"""Validation primitives for ETL data quality checks.

Provides a small framework for validating extracted data prior to loading. It
includes a ``Validator`` base class, several concrete validators, a
``ValidationSequence`` to compose multiple validators, and the structured
``ValidationResult`` object returned from a validation run.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from .schema import Schema, DataType
from algomancy_utils import Logger


class ValidationSeverity(StrEnum):
    """Severity levels used in validation messages."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


_SEVERITY_ORDER = {
    ValidationSeverity.INFO: 0,
    ValidationSeverity.WARNING: 1,
    ValidationSeverity.ERROR: 2,
    ValidationSeverity.CRITICAL: 3,
}


def _severity_at_least(
    severity: ValidationSeverity, threshold: ValidationSeverity
) -> bool:
    return _SEVERITY_ORDER[severity] >= _SEVERITY_ORDER[threshold]


class ValidationError(Exception):
    """Exception raised for validation errors in the data pipeline.

    Retained for backwards-compatibility. The modern flow (``ETLPipeline.run``
    returning ``ETLResult``) no longer raises this exception for data-quality
    failures; callers should inspect ``ETLResult.validation_result`` instead.

    Attributes:
        message: Explanation of the error.
        context: Optional dictionary or object with additional context.
    """

    def __init__(
        self, message: str = "Validation failed.", context: Any = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.context = context

    def __str__(self) -> str:
        base = self.message
        if self.context:
            base += f" Context: {self.context}"
        return base


class ValidationMessage:
    """Container for a validation outcome with optional structured location."""

    __slots__ = ("severity", "message", "table", "column", "row", "code")

    def __init__(
        self,
        severity: ValidationSeverity,
        message: str,
        table: Optional[str] = None,
        column: Optional[str] = None,
        row: Optional[int] = None,
        code: Optional[str] = None,
    ) -> None:
        self.severity = severity
        self.message = self.clean(message)
        self.table = table
        self.column = column
        self.row = row
        self.code = code

    @staticmethod
    def clean(message: str) -> str:
        """Normalize message by escaping newlines/tabs for single-line logs."""
        return message.replace("\n", "\\n").replace("\t", "\\t")

    def __str__(self) -> str:
        loc_parts = []
        if self.table is not None:
            loc_parts.append(f"table={self.table}")
        if self.column is not None:
            loc_parts.append(f"column={self.column}")
        if self.row is not None:
            loc_parts.append(f"row={self.row}")
        if self.code is not None:
            loc_parts.append(f"code={self.code}")
        suffix = f" [{', '.join(loc_parts)}]" if loc_parts else ""
        return f"{self.severity}: {self.message}{suffix}"

    def __repr__(self) -> str:
        return (
            f"ValidationMessage(severity={self.severity!r}, message={self.message!r}, "
            f"table={self.table!r}, column={self.column!r}, row={self.row!r}, "
            f"code={self.code!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ValidationMessage):
            return NotImplemented
        return (
            self.severity == other.severity
            and self.message == other.message
            and self.table == other.table
            and self.column == other.column
            and self.row == other.row
            and self.code == other.code
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": str(self.severity),
            "message": self.message,
            "table": self.table,
            "column": self.column,
            "row": self.row,
            "code": self.code,
        }


@dataclass
class ValidationResult:
    """Structured outcome of a ``ValidationSequence`` run.

    Attributes:
        is_valid: ``True`` if no message met or exceeded the halt threshold.
        messages: All messages collected during the run.
        halt_on: Severity threshold that determined ``is_valid``.
        counts_by_severity: Count of messages per severity level.
    """

    is_valid: bool
    messages: List[ValidationMessage] = field(default_factory=list)
    halt_on: ValidationSeverity = ValidationSeverity.CRITICAL
    counts_by_severity: Dict[str, int] = field(default_factory=dict)

    def messages_by_severity(
        self, severity: ValidationSeverity
    ) -> List[ValidationMessage]:
        """Return all messages matching ``severity``."""
        return [m for m in self.messages if m.severity == severity]

    def messages_at_least(
        self, severity: ValidationSeverity
    ) -> List[ValidationMessage]:
        """Return all messages with severity ``>= severity``."""
        return [m for m in self.messages if _severity_at_least(m.severity, severity)]

    def as_dataframe(self) -> pd.DataFrame:
        """Render messages as a pandas DataFrame for display/inspection."""
        if not self.messages:
            return pd.DataFrame(
                columns=["severity", "message", "table", "column", "row", "code"]
            )
        return pd.DataFrame([m.to_dict() for m in self.messages])

    def __bool__(self) -> bool:
        return self.is_valid

    def __iter__(self) -> Iterable[ValidationMessage]:
        return iter(self.messages)

    def __len__(self) -> int:
        return len(self.messages)


class Validator(ABC):
    """Abstract validator that appends messages during ``validate``."""

    def __init__(self) -> None:
        self._messages: List[ValidationMessage] = []
        self._message_buffer: List[ValidationMessage] = []

    @property
    def messages(self) -> List[ValidationMessage]:
        self.flush_buffer()
        return self._messages

    def add_message(
        self,
        severity: ValidationSeverity,
        message: str,
        table: Optional[str] = None,
        column: Optional[str] = None,
        row: Optional[int] = None,
        code: Optional[str] = None,
    ) -> None:
        self._messages.append(
            ValidationMessage(
                severity, message, table=table, column=column, row=row, code=code
            )
        )

    def buffer_message(
        self,
        severity: ValidationSeverity,
        message: str,
        table: Optional[str] = None,
        column: Optional[str] = None,
        row: Optional[int] = None,
        code: Optional[str] = None,
    ) -> None:
        self._message_buffer.append(
            ValidationMessage(
                severity, message, table=table, column=column, row=row, code=code
            )
        )

    def flush_buffer(self, success_message: Optional[str] = None) -> None:
        """Move buffered messages into the main list; add optional success note."""
        if len(self._message_buffer) == 0 and success_message:
            self.add_message(ValidationSeverity.INFO, success_message)
        else:
            for message in self._message_buffer:
                self._messages.append(message)
            self._message_buffer = []

    @abstractmethod
    def validate(self, data: Dict[str, pd.DataFrame]) -> List[ValidationMessage]:
        """Validate the provided data and return collected messages."""
        raise NotImplementedError


class DefaultValidator(Validator):
    """No-op validator that always returns a single success INFO message."""

    def validate(self, data: Dict[str, pd.DataFrame]) -> List[ValidationMessage]:
        return [ValidationMessage(ValidationSeverity.INFO, "Validation successful")]


class ExtractionSuccessVerification(Validator):
    """Validator that ensures extracted DataFrames are not empty."""

    def validate(self, data: Dict[str, pd.DataFrame]) -> List[ValidationMessage]:
        for name, df in data.items():
            if df.empty:
                self.add_message(
                    ValidationSeverity.CRITICAL,
                    f"Extraction of {name} returned empty DataFrame.",
                    table=name,
                    code="EMPTY_EXTRACTION",
                )
        return self.messages


class SchemaValidator(Validator):
    """Validate DataFrames against a list of ``Schema`` declarations.

    Checks each known table for unexpected columns and dtype mismatches.

    Attributes:
        _schemas: Mapping of file name → ``Schema`` (or subschema).
        _severity: Severity used for column/schema mismatches.
    """

    def __init__(
        self,
        schemas: Optional[List[Schema]] = None,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        super().__init__()
        self._schemas: Optional[Dict[str, Schema]] = (
            {cfg.file_name(): cfg for cfg in schemas} if schemas else None
        )
        self._severity = severity

    def validate(self, data: Dict[str, pd.DataFrame]) -> List[ValidationMessage]:
        if not self._schemas:
            self.add_message(self._severity, "No configurations provided.")
            return self.messages

        dtype_groups: Dict[str, Dict[str, DataType]] = {}
        for cfg in self._schemas.values():
            if cfg.is_single():
                dtype_groups[cfg.file_name()] = cfg.datatypes()
            elif cfg.is_multi():
                for sub_cfg, type_group in cfg.datatype_groups().items():
                    dtype_groups[f"{cfg.file_name()}.{sub_cfg}"] = type_group

        for name, df in data.items():
            if name not in dtype_groups:
                self.buffer_message(
                    self._severity,
                    f"No schema found for {name}.",
                    table=name,
                    code="NO_SCHEMA",
                )
                continue

            type_group: Dict[str, DataType] = dtype_groups[name]
            for col in df.columns:
                if col not in type_group:
                    self.buffer_message(
                        self._severity,
                        f"Column '{col}' not in schema for {name}.",
                        table=name,
                        column=col,
                        code="UNEXPECTED_COLUMN",
                    )
                elif df[col].dtype != type_group[col]:
                    self.buffer_message(
                        ValidationSeverity.WARNING,
                        f"Column '{col}' has incorrect datatype for {name}.",
                        table=name,
                        column=col,
                        code="DTYPE_MISMATCH",
                    )

            self.flush_buffer(
                success_message=f"Schema validation successful for {name}."
            )

        return self.messages


def schema_table_map(schemas: List[Schema]) -> Dict[str, Schema]:
    """Map every expected table name (incl. multi-sheet keys) to its schema class.

    For SINGLE schemas the table key equals the file name. For MULTI schemas
    one entry per sub-schema is produced (``<file_name>.<sub_name>``).
    """
    table_map: Dict[str, Schema] = {}
    for schema in schemas:
        if schema.is_single():
            table_map[schema.file_name()] = schema
        elif schema.is_multi():
            for sub_name in schema.sub_names():
                table_map[f"{schema.file_name()}.{sub_name}"] = schema.get_subschema(
                    sub_name
                )
    return table_map


# Back-compat alias; prefer ``schema_table_map``.
_schema_table_map = schema_table_map


class RequiredColumnsValidator(Validator):
    """Fail when a schema's required columns are missing from the extracted data.

    Emits one structured message per missing column with ``table`` and
    ``column`` populated.

    Attributes:
        _schemas: Schemas to enforce.
        _severity: Severity used for missing-column reports.
    """

    def __init__(
        self,
        schemas: List[Schema],
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        super().__init__()
        self._schemas = schemas
        self._severity = severity

    def validate(self, data: Dict[str, pd.DataFrame]) -> List[ValidationMessage]:
        table_map = _schema_table_map(self._schemas)
        for table_name, schema in table_map.items():
            if table_name not in data:
                continue  # absence of the whole table is a different validator's concern
            df = data[table_name]
            for required in schema.required_columns():
                if required not in df.columns:
                    self.add_message(
                        self._severity,
                        f"Required column '{required}' missing from {table_name}.",
                        table=table_name,
                        column=required,
                        code="MISSING_REQUIRED_COLUMN",
                    )
        return self.messages


def _composite_key(df: pd.DataFrame, columns: List[str]) -> pd.Series:
    """Render a composite key as tuple values for duplicate/null checks."""
    if len(columns) == 1:
        return df[columns[0]]
    return df[columns].apply(tuple, axis=1)


class PrimaryKeyValidator(Validator):
    """Enforce uniqueness and non-null over each schema's primary key.

    Supports joint primary keys. Skips schemas with no declared primary key.

    Attributes:
        _schemas: Schemas to enforce primary-key constraints for.
        _severity: Severity used when violations are detected.
    """

    def __init__(
        self,
        schemas: List[Schema],
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        super().__init__()
        self._schemas = schemas
        self._severity = severity

    def validate(self, data: Dict[str, pd.DataFrame]) -> List[ValidationMessage]:
        table_map = _schema_table_map(self._schemas)
        for table_name, schema in table_map.items():
            pk = list(schema.primary_key())
            if not pk or table_name not in data:
                continue
            df = data[table_name]
            missing_pk_cols = [c for c in pk if c not in df.columns]
            if missing_pk_cols:
                for c in missing_pk_cols:
                    self.add_message(
                        self._severity,
                        f"Primary-key column '{c}' missing from {table_name}.",
                        table=table_name,
                        column=c,
                        code="MISSING_PK_COLUMN",
                    )
                continue

            # Nulls in any PK column
            null_mask = df[pk].isna().any(axis=1)
            for row_idx in df.index[null_mask].tolist():
                self.add_message(
                    self._severity,
                    f"Null value in primary key {tuple(pk)} of {table_name}.",
                    table=table_name,
                    column=",".join(pk),
                    row=int(row_idx),
                    code="PK_NULL",
                )

            # Duplicate composite keys
            key_series = _composite_key(df.loc[~null_mask], pk)
            duplicated_mask = key_series.duplicated(keep=False)
            for row_idx in key_series.index[duplicated_mask].tolist():
                self.add_message(
                    self._severity,
                    f"Duplicate primary key value in {table_name}.",
                    table=table_name,
                    column=",".join(pk),
                    row=int(row_idx),
                    code="PK_DUPLICATE",
                )
        return self.messages


class UniqueValueValidator(Validator):
    """Flag duplicate values within one or more columns of a single table.

    Each column is checked independently (not as a composite key).

    Attributes:
        table: Table name to inspect.
        columns: Column names whose values must be unique.
        severity: Severity used for violations.
    """

    def __init__(
        self,
        table: str,
        columns: List[str],
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        super().__init__()
        self.table = table
        self.columns = list(columns)
        self.severity = severity

    def validate(self, data: Dict[str, pd.DataFrame]) -> List[ValidationMessage]:
        if self.table not in data:
            self.add_message(
                self.severity,
                f"Table '{self.table}' not found for unique-value check.",
                table=self.table,
                code="TABLE_NOT_FOUND",
            )
            return self.messages
        df = data[self.table]
        for col in self.columns:
            if col not in df.columns:
                self.add_message(
                    self.severity,
                    f"Column '{col}' not found in '{self.table}' for unique check.",
                    table=self.table,
                    column=col,
                    code="COLUMN_NOT_FOUND",
                )
                continue
            non_null = df[col].dropna()
            duplicated_mask = non_null.duplicated(keep=False)
            for row_idx in non_null.index[duplicated_mask].tolist():
                self.add_message(
                    self.severity,
                    f"Duplicate value in '{self.table}.{col}'.",
                    table=self.table,
                    column=col,
                    row=int(row_idx),
                    code="DUPLICATE_VALUE",
                )
        return self.messages


class MissingValueValidator(Validator):
    """Flag null cells in columns that are declared non-nullable.

    Attributes:
        table: Table name to inspect.
        columns: Column names that must not be null.
        severity: Severity used for violations.
    """

    def __init__(
        self,
        table: str,
        columns: List[str],
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        super().__init__()
        self.table = table
        self.columns = list(columns)
        self.severity = severity

    def validate(self, data: Dict[str, pd.DataFrame]) -> List[ValidationMessage]:
        if self.table not in data:
            self.add_message(
                self.severity,
                f"Table '{self.table}' not found for missing-value check.",
                table=self.table,
                code="TABLE_NOT_FOUND",
            )
            return self.messages
        df = data[self.table]
        for col in self.columns:
            if col not in df.columns:
                self.add_message(
                    self.severity,
                    f"Column '{col}' not found in '{self.table}' for null check.",
                    table=self.table,
                    column=col,
                    code="COLUMN_NOT_FOUND",
                )
                continue
            null_mask = df[col].isna()
            for row_idx in df.index[null_mask].tolist():
                self.add_message(
                    self.severity,
                    f"Null value in '{self.table}.{col}'.",
                    table=self.table,
                    column=col,
                    row=int(row_idx),
                    code="NULL_VALUE",
                )
        return self.messages


class ForeignKeyValidator(Validator):
    """Cross-table integrity check.

    Verifies that every (non-null) value of ``left_table[left_col]`` exists
    in ``right_table[right_col]``. Supports composite keys when ``left_col``
    and ``right_col`` are lists of equal length.

    Attributes:
        left_table: Table that holds the foreign key values.
        left_col: Column name (or list of names) on the left side.
        right_table: Table that holds the referenced values.
        right_col: Column name (or list of names) on the right side.
        severity: Severity used when a value is not found.
    """

    def __init__(
        self,
        left_table: str,
        left_col,
        right_table: str,
        right_col,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        super().__init__()
        self.left_table = left_table
        self.right_table = right_table
        self.left_col: List[str] = (
            [left_col] if isinstance(left_col, str) else list(left_col)
        )
        """Column name (or list of names) on the left side."""
        self.right_col: List[str] = (
            [right_col] if isinstance(right_col, str) else list(right_col)
        )
        """Column name (or list of names) on the right side."""
        if len(self.left_col) != len(self.right_col):
            raise ValueError(
                "left_col and right_col must have the same length "
                f"(got {len(self.left_col)} and {len(self.right_col)})."
            )
        self.severity = severity

    def _bail(self, msg: str, **kwargs) -> None:
        self.add_message(self.severity, msg, **kwargs)

    def validate(self, data: Dict[str, pd.DataFrame]) -> List[ValidationMessage]:
        if self.left_table not in data:
            self._bail(
                f"Left table '{self.left_table}' not found for FK check.",
                table=self.left_table,
                code="TABLE_NOT_FOUND",
            )
            return self.messages
        if self.right_table not in data:
            self._bail(
                f"Right table '{self.right_table}' not found for FK check.",
                table=self.right_table,
                code="TABLE_NOT_FOUND",
            )
            return self.messages

        left_df = data[self.left_table]
        right_df = data[self.right_table]

        for col in self.left_col:
            if col not in left_df.columns:
                self._bail(
                    f"Left column '{col}' missing from {self.left_table}.",
                    table=self.left_table,
                    column=col,
                    code="COLUMN_NOT_FOUND",
                )
                return self.messages
        for col in self.right_col:
            if col not in right_df.columns:
                self._bail(
                    f"Right column '{col}' missing from {self.right_table}.",
                    table=self.right_table,
                    column=col,
                    code="COLUMN_NOT_FOUND",
                )
                return self.messages

        left_keys = _composite_key(left_df, self.left_col)
        right_keys = set(_composite_key(right_df, self.right_col).dropna().tolist())

        # Skip nulls — they should be caught by MissingValueValidator instead.
        non_null_mask = ~left_df[self.left_col].isna().any(axis=1)
        for row_idx in left_df.index[non_null_mask].tolist():
            value = left_keys.loc[row_idx]
            if value not in right_keys:
                self._bail(
                    (
                        f"Foreign key {tuple(self.left_col)}={value!r} in "
                        f"{self.left_table} has no match in "
                        f"{self.right_table}.{tuple(self.right_col)}."
                    ),
                    table=self.left_table,
                    column=",".join(self.left_col),
                    row=int(row_idx),
                    code="FK_VIOLATION",
                )
        return self.messages

    @classmethod
    def from_schemas(
        cls,
        schemas: Iterable[type],
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> List["ForeignKeyValidator"]:
        """Build a list of validators from ``Column.foreign_key`` declarations.

        Walks each schema's columns; for every column with a non-null
        ``foreign_key`` declaration, returns a ``ForeignKeyValidator``
        instance covering that relation. Columns sharing the same parent
        table on the same schema are collapsed into a single composite-key
        validator.

        Args:
            schemas: Iterable of ``Schema`` subclasses.
            severity: Severity for emitted FK-violation messages.

        Returns:
            List of ``ForeignKeyValidator`` instances, one per derived
            relation. The list is empty if no schema declares a FK.
        """
        # Local import to avoid a circular import at module load time.
        from .relations import resolve_relations_from_schemas

        relations = resolve_relations_from_schemas(list(schemas))
        return [
            cls(
                left_table=r.child_table,
                left_col=list(r.child_cols),
                right_table=r.parent_table,
                right_col=list(r.parent_cols),
                severity=severity,
            )
            for r in relations
        ]


class ValidationSequence:
    """A sequence of validators executed in order with message aggregation.

    Attributes:
        halt_on: Severity at or above which the run is considered invalid.
            Defaults to ``ValidationSeverity.CRITICAL``.
    """

    def __init__(
        self,
        validators: Optional[List[Validator]] = None,
        logger: Optional[Logger] = None,
        halt_on: ValidationSeverity = ValidationSeverity.CRITICAL,
    ) -> None:
        self._messages: List[ValidationMessage] = []
        self._validators: List[Validator] = []
        self._completed = False
        self._logger = logger
        self.halt_on = halt_on
        if validators:
            self.add_validators(validators)

    @property
    def is_valid(self) -> bool:
        """Return True when completed and no message met ``halt_on`` threshold."""
        if not self._completed:
            return False
        return not any(
            _severity_at_least(msg.severity, self.halt_on) for msg in self._messages
        )

    @property
    def messages(self) -> List[ValidationMessage]:
        return self._messages

    @property
    def completed(self) -> bool:
        return self._completed

    def run_validation(self, data: Dict[str, pd.DataFrame]) -> ValidationResult:
        """Execute validators, collect messages, and return a ``ValidationResult``."""
        for validator in self._validators:
            messages = validator.validate(data=data)
            self._add_messages(messages)
        self._completed = True

        counts = Counter(str(m.severity) for m in self._messages)
        return ValidationResult(
            is_valid=self.is_valid,
            messages=list(self._messages),
            halt_on=self.halt_on,
            counts_by_severity=dict(counts),
        )

    def add_validators(self, validators: List[Validator]) -> None:
        """Append multiple validators to the sequence."""
        for validator in validators:
            self._validators.append(validator)

    def add_validator(self, validator: Validator) -> None:
        """Append a single validator to the sequence."""
        self._validators.append(validator)

    def _add_messages(self, messages: List[ValidationMessage]) -> None:
        for message in messages:
            self._add_message(message)

    def _add_message(self, message: ValidationMessage) -> None:
        self._messages.append(message)
        self._log(message)

    def _log(self, validation_message: ValidationMessage) -> None:
        """Log a validation message through the configured logger, if any."""
        if not self._logger:
            return None
        match validation_message.severity:
            case ValidationSeverity.INFO:
                self._logger.log(validation_message.message)
            case ValidationSeverity.WARNING:
                self._logger.warning(validation_message.message)
            case ValidationSeverity.ERROR:
                self._logger.error(validation_message.message)
            case ValidationSeverity.CRITICAL:
                self._logger.error("[CRITICAL] " + validation_message.message)
        return None
