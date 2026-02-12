"""Validation primitives for ETL data quality checks.

Provides a small framework for validating extracted data prior to loading. It
includes a ``Validator`` base class, a few concrete validators, and a
``ValidationSequence`` to compose multiple validators and collect messages.
"""

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import List, Dict

import pandas as pd

from .schema import Schema, DataType
from algomancy_utils import Logger


class ValidationSeverity(StrEnum):
    """Severity levels used in validation messages."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ValidationError(Exception):
    """
    Exception raised for validation errors in the data pipeline.

    Attributes:
        message: explanation of the error
        context: optional dictionary or object with additional context info
    """

    def __init__(self, message="Validation failed.", context=None):
        super().__init__(message)
        self.message = message
        self.context = context

    def __str__(self):
        base = self.message
        if self.context:
            base += f" Context: {self.context}"
        return base


class ValidationMessage:
    """Simple container for a validation message and its severity."""

    def __init__(self, severity: ValidationSeverity, message: str) -> None:
        self.severity = severity
        self.message = self.clean(message)

    @staticmethod
    def clean(message):
        """Normalize message by escaping newlines/tabs for single-line logs."""
        return message.replace("\n", "\\n").replace("\t", "\\t")

    def __str__(self):
        return f"{self.severity}: {self.message}"


class Validator(ABC):
    """Abstract validator that appends messages during ``validate``."""

    def __init__(self) -> None:
        self._messages = []
        self._message_buffer = []
        pass

    @property
    def messages(self) -> List[ValidationMessage]:
        self.flush_buffer()
        return self._messages

    def add_message(self, severity: ValidationSeverity, message: str) -> None:
        self._messages.append(ValidationMessage(severity, message))

    def buffer_message(self, severity: ValidationSeverity, message: str) -> None:
        self._message_buffer.append(ValidationMessage(severity, message))

    def flush_buffer(self, success_message: str = None) -> None:
        """Move buffered messages into the main list; add optional success note."""
        if len(self._message_buffer) == 0 and success_message:
            self.add_message(ValidationSeverity.INFO, success_message)
        else:
            for message in self._message_buffer:
                self.add_message(message.severity, message.message)
            self._message_buffer = []

    @abstractmethod
    def validate(self, data: Dict[str, pd.DataFrame]) -> List[ValidationMessage]:
        """Validate the provided data and return collected messages."""
        pass


class DefaultValidator(Validator):
    """No-op validator that always returns a single success INFO message."""

    def __init__(self) -> None:
        super().__init__()

    def validate(self, data: Dict[str, pd.DataFrame]) -> List[ValidationMessage]:
        return [ValidationMessage(ValidationSeverity.INFO, "Validation successful")]


class ExtractionSuccessVerification(Validator):
    """Validator that ensures extracted DataFrames are not empty."""

    def __init__(self) -> None:
        super().__init__()

    def validate(self, data: Dict[str, pd.DataFrame]) -> List[ValidationMessage]:
        for name, df in data.items():
            if df.empty:
                self.add_message(
                    ValidationSeverity.CRITICAL,
                    f"Extraction of {name} returned empty DataFrame.",
                )
        return self.messages


class SchemaValidator(Validator):
    """
    Handles the validation of data against predefined schemas.

    The InputConfigurationValidator class is responsible for ensuring that data provided as input
    conforms to a set of user-defined schemas. It checks the presence of schemas and validates
    the structure and data types of each column within the data. Validation results are
    reported as messages, which include information about errors or successful validations.

    Attributes:
        _schemas (Dict[str, Schema], optional): dictionary of Schema objects
        _severity (ValidationSeverity, optional): configurable severity level for validation messages
                    yielded by this validator. Defaults to ValidationSeverity.ERROR.

    """

    def __init__(
        self,
        schemas: List[Schema] = None,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        super().__init__()

        self._schemas: Dict[str, Schema] | None = (
            {cfg.file_name: cfg for cfg in schemas} if schemas else None
        )

        self._severity = severity

    def validate(self, data: Dict[str, pd.DataFrame]) -> List[ValidationMessage]:
        if not self._schemas:
            self.add_message(self._severity, "No configurations provided.")
            return self.messages

        dtype_groups = {}
        for cfg in self._schemas.values():
            if cfg.is_single():
                dtype_groups[cfg.file_name] = cfg.datatypes
            elif cfg.is_multi():
                for sub_cfg, type_group in cfg.datatype_groups.items():
                    dtype_groups[f"{cfg.file_name}.{sub_cfg}"] = type_group

        for name, df in data.items():
            if name not in dtype_groups:
                self.buffer_message(self._severity, f"No schema found for {name}.")
                continue

            type_group: dict[str, DataType] = dtype_groups[name]
            for col in df.columns:
                if col not in type_group:
                    self.buffer_message(
                        self._severity, f"Column '{col}' not in schema for {name}."
                    )
                elif df[col].dtype != type_group[col]:
                    self.buffer_message(
                        ValidationSeverity.WARNING,
                        f"Column '{col}' has incorrect datatype for {name}.",
                    )

            self.flush_buffer(
                success_message=f"Schema validation successful for {name}."
            )

        return self.messages


class ValidationSequence:
    """A sequence of validators executed in order with message aggregation."""

    def __init__(self, validators: List[Validator] = None, logger: Logger = None):
        self._messages: List[ValidationMessage] = []
        self._validators: List[Validator] = []
        self._completed = False
        if validators:
            self.add_validators(validators)
        if logger:
            self._logger = logger
        else:
            self._logger = None

    @property
    def is_valid(self) -> bool:
        """Return True when completed and no CRITICAL messages are present."""
        if not self._completed:
            return False

        return (
            len(
                [
                    msg
                    for msg in self._messages
                    if (msg.severity == ValidationSeverity.CRITICAL)
                ]
            )
            == 0
        )

    @property
    def messages(self) -> List[ValidationMessage]:
        return self._messages

    @property
    def completed(self) -> bool:
        return self._completed

    def run_validation(
        self, data: Dict[str, pd.DataFrame]
    ) -> (bool, List[ValidationMessage]):
        """Execute validators, collect messages, and return (is_valid, messages)."""
        for validator in self._validators:
            messages = validator.validate(data=data)
            self._add_messages(messages)
        self._completed = True
        return self.is_valid, self._messages

    def add_validators(self, validators: List[Validator]):
        """Append multiple validators to the sequence."""
        for validator in validators:
            self._validators.append(validator)

    def add_validator(self, validator: Validator):
        """Append a single validator to the sequence."""
        self._validators.append(validator)

    def _add_messages(self, messages: List[ValidationMessage]):
        for message in messages:
            self._add_message(message)

    def _add_message(self, message: ValidationMessage):
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
