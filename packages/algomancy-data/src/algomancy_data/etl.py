# --- Abstract Factory ---
from algomancy_data.transformer import TransformationSequence
from abc import ABC, abstractmethod
from typing import Dict, List

from algomancy_utils import Logger

from .schema import Schema
from .datasource import BASE_DATA_BOUND, DataClassification
from .extractor import ExtractionSequence
from .file import File
from .loader import Loader
from .validator import ValidationError, ValidationSequence
from .inputfileconfiguration import (
    InputFileConfiguration,
    SingleInputFileConfiguration,
    MultiInputFileConfiguration,
)


class ETLPipeline:
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

    def run(self) -> BASE_DATA_BOUND:
        """
        Executes an ETL (Extract, Transform, Load) job by coordinating the extraction of data, validation,
        transformation, and loading into a DataSource. It uses extractors to collect data, a validator
        to ensure the integrity of the data, transformers to modify the data as necessary, and a loader
        to complete the ETL pipeline by saving the processed data into a DataSource.

        Raises:
            ValidationException: Raised when a critical validation error occurs during the validation
            step, indicating that the data does not meet required criteria.

        Returns:
            BASE_DATA_BOUND: The resultant DataSource object containing the processed and loaded data.
        """
        # Extraction
        raw_data = self.extraction_sequence.data

        # Validation
        is_valid, validation_messages = self.validation_sequence.run_validation(
            raw_data
        )

        if not is_valid:
            raise ValidationError(
                "A critical validation error occurred. See log for details."
            )

        # Transformation
        transformed_data = self.transformation_sequence.run_transformation(raw_data)

        # Load into DataSource
        datasource = self.loader.load(
            name=self.destination_name,
            data=transformed_data,
            validation_messages=validation_messages,
            ds_type=DataClassification.MASTER_DATA,
        )

        if self.logger:
            self.logger.log("ETL job completed.")
        return datasource


class ETLConstructionError(Exception):
    def __init__(self, message):
        super().__init__(message)


class ETLFactory(ABC):
    def __init__(self, input_configurations: List[InputFileConfiguration], logger):
        self.input_configurations = input_configurations
        # self.schemas = {cfg.file_name: cfg.file_schema for cfg in input_configurations} # todo is this used?
        self.logger = logger

    @property
    def configs_dct(self) -> Dict[str, InputFileConfiguration]:
        return {cfg.file_name: cfg for cfg in self.input_configurations}

    def get_schemas(self, file_name: str) -> Dict[str, Schema] | Schema:
        try:
            cfg = self.configs_dct[file_name]
        except KeyError:
            raise ETLConstructionError(
                f"No input configuration available for {file_name}."
            )

        if isinstance(cfg, SingleInputFileConfiguration):
            return cfg.file_schema
        elif isinstance(cfg, MultiInputFileConfiguration):
            return cfg.file_schemas
        else:
            raise ETLConstructionError(
                f"{file_name} does not have a valid input file configuration"
            )

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
        e_seq = self.create_extraction_sequence(files)
        v_seq = self.create_validation_sequence()
        t_seq = self.create_transformation_sequence()
        loader = self.create_loader()
        return ETLPipeline(dataset_name, e_seq, v_seq, t_seq, loader, logger)
