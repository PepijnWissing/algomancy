from abc import ABC, abstractmethod
from enum import StrEnum
from typing import List, Dict

import pandas as pd

from algomancy.dashboardlogger.logger import Logger
from algomancy.dataengine.inputfileconfiguration import InputFileConfiguration


class ValidationSeverity(StrEnum):
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
    def __init__(self, severity: ValidationSeverity, message: str) -> None:
        self.severity = severity
        self.message = self.clean(message)

    @staticmethod
    def clean(message):
        return message.replace("\n", "\\n").replace("\t", "\\t")

    def __str__(self):
        return f"{self.severity}: {self.message}"


class Validator(ABC):
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
        if len(self._message_buffer) == 0 and success_message:
            self.add_message(ValidationSeverity.INFO, success_message)
        else:
            for message in self._message_buffer:
                self.add_message(message.severity, message.message)
            self._message_buffer = []

    @abstractmethod
    def validate(self, data: Dict[str, pd.DataFrame]) -> List[ValidationMessage]:
        pass


class DefaultValidator(Validator):
    def __init__(self) -> None:
        super().__init__()

    def validate(self, data: Dict[str, pd.DataFrame]) -> List[ValidationMessage]:
        return [ValidationMessage(ValidationSeverity.INFO, "Validation successful")]


class ExtractionSuccessVerification(Validator):
    def __init__(self) -> None:
        super().__init__()

    def validate(self, data: Dict[str, pd.DataFrame]) -> List[ValidationMessage]:
        for name, df in data.items():
            if df.empty:
                self.add_message(
                        ValidationSeverity.CRITICAL,
                        f"Extraction of {name} returned empty DataFrame."
                    )
        return self.messages


class InputConfigurationValidator(Validator):
    """
    Handles the validation of data against predefined schemas.

    The InputConfigurationValidator class is responsible for ensuring that data provided as input
    conforms to a set of user-defined schemas. It checks the presence of schemas and validates
    the structure and data types of each column within the data. Validation results are
    reported as messages, which include information about errors or successful validations.

    Attributes:
        _configs (Dict[str, InputFileConfiguration], optional): dictionary of InputFileConfiguration objects
        _severity (ValidationSeverity, optional): configurable severity level for validation messages
                    yielded by this validator. Defaults to ValidationSeverity.ERROR.

    """
    def __init__(
            self,
            configs: List[InputFileConfiguration] = None,
            severity: ValidationSeverity = ValidationSeverity.ERROR
    ) -> None:
        super().__init__()

        self._configs: Dict[str, InputFileConfiguration] | None = \
            {cfg.file_name: cfg for cfg in configs} if configs else None

        self._severity = severity

    def validate(self, data: Dict[str, pd.DataFrame]) -> List[ValidationMessage]:
        if not self._configs:
            self.add_message(
                self._severity, "No configurations provided."
            )
            return self.messages

        for name, df in data.items():
            if name not in self._configs:
                self.buffer_message(
                    self._severity, f"No configuration found for {name}."
                )
                continue

            config = self._configs[name]
            if not isinstance(config, InputFileConfiguration):
                self.buffer_message(
                    self._severity, f"Schema for {name} is not a Schema object."
                )
                continue

            schema = config.file_schema
            for col in df.columns:
                if col not in schema.datatypes:
                    self.buffer_message(
                            self._severity, f"Column '{col}' not in schema for {name}."
                        )
                elif df[col].dtype != schema.datatypes[col]:
                    self.buffer_message(
                            ValidationSeverity.WARNING, f"Column '{col}' has incorrect datatype for {name}."
                        )

            self.flush_buffer(success_message=f"Schema validation successful for {name}.")

        return self.messages


class ValidationSequence:
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
        if not self._completed:
            return False

        return len([msg for msg in self._messages if (msg.severity == ValidationSeverity.CRITICAL)]) == 0

    @property
    def messages(self) -> List[ValidationMessage]:
        return self._messages

    @property
    def completed(self) -> bool:
        return self._completed

    def run_validation(self, data: Dict[str, pd.DataFrame]) -> (bool, List[ValidationMessage]):
        for validator in self._validators:
            messages = validator.validate(data=data)
            self._add_messages(messages)
        self._completed = True
        return self.is_valid, self._messages

    def add_validators(self, validators: List[Validator]):
        for validator in validators:
            self._validators.append(validator)

    def add_validator(self, validator: Validator):
        self._validators.append(validator)

    def _add_messages(self, messages: List[ValidationMessage]):
        for message in messages:
            self._add_message(message)

    def _add_message(self, message: ValidationMessage):
        self._messages.append(message)
        self._log(message)

    def _log(self, validation_message: ValidationMessage) -> None:
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
