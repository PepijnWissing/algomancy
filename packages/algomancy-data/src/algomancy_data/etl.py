"""ETL pipeline composition and abstract factory.

This module defines ``ETLPipeline`` which orchestrates the Extract-Validate-
Transform-Load steps, and ``ETLFactory`` that builds the pipeline components
for a concrete dataset configuration.

ETLPipeline.run() returns an ``ETLResult`` describing the outcome of the
job. Data-quality failures (validation, missing/malformed inputs) are
reported via ``status='failed'`` rather than as exceptions. Programmer
errors (unexpected ``KeyError``/``AttributeError``/``TypeError`` etc. from
user-supplied components) still propagate so that real defects are not
masked.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Type

from algomancy_utils import Logger

from algomancy_data.transformer import TransformationSequence
from .schema import Schema
from .datasource import BASEDATASOURCE, DataClassification
from .extractor import ConversionIssue, ExtractionSequence
from .file import File
from .loader import Loader
from .validator import (
    ValidationError,
    ValidationMessage,
    ValidationResult,
    ValidationSequence,
    ValidationSeverity,
)


# Exceptions originating in the ETL machinery itself that represent
# *expected* data-quality failures (missing files, malformed contents,
# schema/file mismatches) — these are caught and converted to ETLResult
# with status='failed'. Anything outside this list is treated as a
# programmer error and propagated.
_EXPECTED_ETL_EXCEPTIONS: tuple = (
    FileNotFoundError,
    ValidationError,
)


@dataclass
class ETLResult:
    """Structured outcome of an ``ETLPipeline.run()`` invocation.

    Attributes:
        status: ``'success'`` if the run completed and validation passed;
            ``'failed'`` if a data-quality issue was detected.
        datasource: Loaded destination object (``None`` on failure).
        validation_result: Messages and counts from the validation step.
            Always present, even when extraction never produced data.
        raised: Original exception when a recognised data-quality
            exception was caught and converted to a failure. ``None``
            otherwise. Programmer errors are not captured here — they
            propagate from ``run()`` unchanged.
    """

    status: Literal["success", "failed"]
    datasource: Optional[BASEDATASOURCE] = None
    validation_result: Optional[ValidationResult] = None
    raised: Optional[Exception] = None

    @property
    def is_success(self) -> bool:
        return self.status == "success"

    @property
    def is_failure(self) -> bool:
        return self.status == "failed"

    @property
    def messages(self) -> List[ValidationMessage]:
        """Convenience accessor for ``validation_result.messages``."""
        if self.validation_result is None:
            return []
        return self.validation_result.messages


def _empty_validation_result(
    failure_message: str,
    severity: ValidationSeverity = ValidationSeverity.CRITICAL,
    code: Optional[str] = None,
    table: Optional[str] = None,
) -> ValidationResult:
    """Build a ValidationResult that captures a pre-validation failure."""
    msg = ValidationMessage(severity, failure_message, table=table, code=code)
    return ValidationResult(
        is_valid=False,
        messages=[msg],
        halt_on=ValidationSeverity.CRITICAL,
        counts_by_severity={str(severity): 1},
    )


class ETLPipeline:
    """Coordinates a single end-to-end ETL job."""

    def __init__(
        self,
        destination_name: str,
        extraction_sequence: ExtractionSequence,
        validation_sequence: ValidationSequence,
        transformation_sequence: TransformationSequence,
        loader: Loader,
        logger: Logger,
    ) -> None:
        self.destination_name = destination_name
        self.extraction_sequence = extraction_sequence
        self.validation_sequence = validation_sequence
        self.transformation_sequence = transformation_sequence
        self.loader = loader
        self.logger = logger

    def run(self) -> ETLResult:
        """Execute the ETL job and return an ``ETLResult``.

        Orchestrates Extraction → Validation → Transformation → Load.

        Returns:
            ETLResult: ``status='success'`` with a loaded ``datasource`` when
            the job completes and validation passes; ``status='failed'``
            (with messages on ``validation_result``) when a data-quality
            issue is detected.

        Raises:
            Exception: Programmer errors (``KeyError``, ``AttributeError``,
                ``TypeError`` and anything else not classified as an expected
                data-quality failure) propagate so that real defects are not
                masked. Use validators for data-quality checks instead.
        """
        # ---- Extraction (expected failures: missing/malformed files) ----
        try:
            raw_data = self.extraction_sequence.data
        except _EXPECTED_ETL_EXCEPTIONS as exc:
            if self.logger:
                self.logger.error(f"Extraction failed: {exc}")
            return ETLResult(
                status="failed",
                datasource=None,
                validation_result=_empty_validation_result(
                    f"Extraction failed: {exc}", code="EXTRACTION_FAILED"
                ),
                raised=exc,
            )

        # Drain dtype-conversion failures from the extraction step so they
        # are surfaced as validation messages rather than silent NaNs.
        conversion_messages = self._conversion_issue_messages(
            self.extraction_sequence.conversion_issues
        )

        # ---- Validation (never raises; surfaces via ValidationResult) ----
        validation_result: ValidationResult = self.validation_sequence.run_validation(
            raw_data
        )
        if conversion_messages:
            validation_result = _augment_with_messages(
                validation_result, conversion_messages
            )

        if not validation_result.is_valid:
            if self.logger:
                self.logger.error(
                    f"Validation failed: {validation_result.counts_by_severity}"
                )
            return ETLResult(
                status="failed",
                datasource=None,
                validation_result=validation_result,
                raised=None,
            )

        # ---- Transformation / Load -----------------------------------
        # Programmer errors in user-supplied transformers/loaders propagate.
        transformed_data = self.transformation_sequence.run_transformation(raw_data)
        datasource = self.loader.load(
            name=self.destination_name,
            data=transformed_data,
            validation_messages=validation_result.messages,
            ds_type=DataClassification.MASTER_DATA,
        )

        if self.logger:
            self.logger.log("ETL job completed.")
        return ETLResult(
            status="success",
            datasource=datasource,
            validation_result=validation_result,
            raised=None,
        )

    @staticmethod
    def _conversion_issue_messages(
        issues: List[ConversionIssue],
    ) -> List[ValidationMessage]:
        """Translate dtype-conversion failures into ERROR ValidationMessages."""
        return [
            ValidationMessage(
                ValidationSeverity.ERROR,
                f"Could not convert column '{issue.column}' to {issue.target_type}: {issue.reason}",
                table=issue.table or None,
                column=issue.column,
                code="CONVERSION_FAILED",
            )
            for issue in issues
        ]


def _augment_with_messages(
    result: ValidationResult, extra: List[ValidationMessage]
) -> ValidationResult:
    """Return a new ValidationResult with extra messages folded in."""
    merged_messages = list(result.messages) + list(extra)
    counts: Dict[str, int] = dict(result.counts_by_severity)
    for msg in extra:
        key = str(msg.severity)
        counts[key] = counts.get(key, 0) + 1

    from .validator import (
        _severity_at_least,
    )  # local import to avoid cycle on type checkers

    is_valid = result.is_valid and not any(
        _severity_at_least(m.severity, result.halt_on) for m in extra
    )
    return ValidationResult(
        is_valid=is_valid,
        messages=merged_messages,
        halt_on=result.halt_on,
        counts_by_severity=counts,
    )


class ETLConstructionError(Exception):
    """Raised when the ETL pipeline cannot be constructed."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ETLFactory(ABC):
    """Abstract factory that constructs ETL sequences and loader."""

    def __init__(self, schemas: List[Type[Schema]], logger: Optional[Logger] = None):
        self.schemas = schemas
        self.logger = logger

    @property
    def schemas_dct(self) -> Dict[str, Schema]:
        """Return a mapping from file name to its schema."""
        return {schema.file_name(): schema for schema in self.schemas}

    def get_schema(self, file_name: str) -> Dict[str, Schema] | Schema:
        """Return schema(s) for the given file name based on configuration.

        Args:
            file_name: Logical file name as defined in a schema.

        Returns:
            Schema or mapping of sub-name to Schema depending on the
            configuration type (single or multi).

        Raises:
            ETLConstructionError: If no configuration exists or it is invalid.
        """
        try:
            schema = self.schemas_dct[file_name]
        except KeyError:
            raise ETLConstructionError(f"No Schema available for {file_name}.")

        return schema

    @abstractmethod
    def create_extraction_sequence(self, files: Dict[str, File]) -> ExtractionSequence:
        pass

    @abstractmethod
    def create_validation_sequence(self) -> ValidationSequence:
        pass

    @abstractmethod
    def create_transformation_sequence(self) -> TransformationSequence:
        pass

    @abstractmethod
    def create_loader(self) -> Loader:
        pass

    def build_pipeline(
        self, dataset_name: str, files: Dict[str, File], logger: Logger
    ) -> ETLPipeline:
        """Assemble and return an ``ETLPipeline`` instance.

        Args:
            dataset_name: Destination dataset name.
            files: Mapping of logical file names to ``File`` objects.
            logger: Logger for the pipeline.

        Returns:
            ETLPipeline ready to run.
        """
        e_seq = self.create_extraction_sequence(files)
        v_seq = self.create_validation_sequence()
        t_seq = self.create_transformation_sequence()
        loader = self.create_loader()
        return ETLPipeline(dataset_name, e_seq, v_seq, t_seq, loader, logger)
