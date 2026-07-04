from typing import Dict, Optional

import algomancy_data as de
from algomancy_data import File, Schema
from algomancy_data.extractor import ExtractionSequence
from algomancy_data.transformer import TransformationSequence
from algomancy_utils import Logger


class PlaceholderETLFactory(de.ETLFactory):
    @classmethod
    def create_extraction_sequence(
        cls,
        files: Dict[str, File] | None = None,
        schemas: Dict[str, Schema] | None = None,
        logger: Optional[Logger] = None,
    ) -> ExtractionSequence:
        return ExtractionSequence(logger=logger)

    @classmethod
    def create_transformation_sequence(
        cls,
        schemas: Dict[str, Schema] | None = None,
        logger: Optional[Logger] = None,
    ) -> TransformationSequence:
        return TransformationSequence(logger=logger)

    @classmethod
    def create_validation_sequence(
        cls,
        schemas: Dict[str, Schema],
        logger: Optional[Logger] = None,
    ) -> de.ValidationSequence:
        return de.ValidationSequence(logger=logger)

    @classmethod
    def create_loader(
        cls,
        logger: Optional[Logger] = None,
    ) -> de.Loader:
        return de.DataSourceLoader(logger)
