# --- Abstract Factory ---
from abc import ABC, abstractmethod
from typing import Dict, List

from algomancy.dataengine.schema import Schema
from algomancy.dataengine.datasource import DataSource, DataSourceType
from algomancy.dataengine.extractor import Extractor
from algomancy.dataengine.file import File
from algomancy.dataengine.loader import Loader
from algomancy.dataengine.transformer import Transformer
from algomancy.dataengine.validator import Validator, ValidationError, ValidationSequence
from algomancy.dataengine.inputfileconfiguration import InputFileConfiguration, SingleInputFileConfiguration, \
    MultiInputFileConfiguration
from algomancy.dashboardlogger.logger import Logger


class ETLPipeline:
    def __init__(
            self,
            destination_name: str,
            extractors: Dict[str, Extractor],
            validation_sequence: ValidationSequence,
            transformers: List[Transformer],  #todo refactor to transformationsequence
            loader: Loader,
            logger: Logger
    ) -> None:
        self.destination_name = destination_name
        self.extractors = extractors
        self.validation_sequence = validation_sequence
        self.transformers = transformers
        self.loader = loader
        self.logger = logger

    def run(self) -> DataSource:
        """
        Executes an ETL (Extract, Transform, Load) job by coordinating the extraction of data, validation,
        transformation, and loading into a DataSource. It uses extractors to collect data, a validator
        to ensure the integrity of the data, transformers to modify the data as necessary, and a loader
        to complete the ETL pipeline by saving the processed data into a DataSource.

        Raises:
            ValidationException: Raised when a critical validation error occurs during the validation
            step, indicating that the data does not meet required criteria.

        Returns:
            DataSource: The resultant DataSource object containing the processed and loaded data.
        """
        # Extraction
        data = {}
        for extractor in self.extractors.values():
            dfs = extractor.extract()
            data.update(dfs)

        # Validation
        is_valid, validation_messages = self.validation_sequence.run_validation(data)

        if not is_valid:
            raise ValidationError("A critical validation error occurred. See log for details.")

        # Transformation
        for transformer in self.transformers:
            transformer.transform(data)

        # Load into DataSource
        datasource = self.loader.load(
            name=self.destination_name,
            data=data,
            validation_messages=validation_messages,
            ds_type=DataSourceType.MASTER_DATA,
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
            raise ETLConstructionError(f"No input configuration available for {file_name}.")

        if isinstance(cfg, SingleInputFileConfiguration):
            return cfg.file_schema
        elif isinstance(cfg, MultiInputFileConfiguration):
            return cfg.file_schemas
        else:
            raise ETLConstructionError(f"{file_name} does not have a valid input file configuration")

    @abstractmethod
    def create_extractors(self, files: Dict[str, File]) -> Dict[str, Extractor]:
        pass

    @abstractmethod
    def create_validation_sequence(self) -> ValidationSequence:
        pass

    @abstractmethod
    def create_transformers(self) -> List[Transformer]:
        pass

    @abstractmethod
    def create_loader(self) -> Loader:
        pass

    def build_pipeline(self, dataset_name: str, files: Dict[str, File], logger: Logger) -> ETLPipeline:
        extractors = self.create_extractors(files)
        validations = self.create_validation_sequence()
        transformers = self.create_transformers()
        loader = self.create_loader()
        return ETLPipeline(dataset_name, extractors, validations, transformers, loader, logger)
