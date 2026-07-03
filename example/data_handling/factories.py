"""ETL factory for the example app.

Both example files (``sku_data.csv`` and ``warehouse_layout.csv``) use a
``;`` separator instead of the default ``,``, so the extraction sequence
is hand-wired for both. Validation and loading inherit the framework
defaults; transformation keeps the standard clean-up chain so users see
how transformers are composed.

For richer ETL feature showcases (cascade-drop FK chains, multi-sheet
XLSX, JSON-multi parent/child extraction, custom validators), see
``packages/algomancy-data/tests/test_disk_etl_fixtures.py`` and the
in-memory unit tests in the same directory.
"""

from typing import Dict, TypeVar, cast

from algomancy_data import (
    CSVFile,
    File,
    OptionalColumnGuard,
    SimpleETLFactory,
)
from algomancy_data.extractor import (
    CSVSingleExtractor,
    ExtractionSequence,
)
from algomancy_data.transformer import (
    CleanTransformer,
    TransformationSequence,
)

F = TypeVar("F", bound=File)


class ExampleETLFactory(SimpleETLFactory):
    """Minimal factory wiring two ``;``-separated CSV files.

    Inherits default loader and validators
    (``RequiredColumnsValidator`` + ``SchemaValidator`` +
    ``PrimaryKeyValidator``, the last one added automatically because
    both schemas declare a primary key).
    """

    def create_extraction_sequence(
        self,
        files: Dict[str, F],
    ) -> ExtractionSequence:
        sequence = ExtractionSequence(logger=self.logger)
        for name in ("sku_data", "warehouse_layout"):
            if name in files:
                sequence.add_extractor(
                    CSVSingleExtractor(
                        file=cast(CSVFile, files[name]),
                        schema=self.get_schema(name),
                        separator=";",
                        logger=self.logger,
                    )
                )
        return sequence

    def create_transformation_sequence(self) -> TransformationSequence:
        sequence = TransformationSequence(logger=self.logger)
        sequence.add_transformer(
            OptionalColumnGuard(schemas=self.schemas, logger=self.logger)
        )
        sequence.add_transformer(CleanTransformer(self.logger))
        return sequence
