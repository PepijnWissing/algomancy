"""Example ETL factory showcasing M2–M5 features.

The factory inherits from :class:`SimpleETLFactory` and reuses the
default validation sequence wherever possible. Extraction is overridden
because the CSV files use a semicolon separator and the inventory XLSX
references a specific sheet by index — everything else lives on the
``ETLFactory`` defaults (registry-driven extractor lookup, default
validators, no-op transformer, ``DataSourceLoader``).
"""

from typing import Dict, TypeVar, cast

from algomancy_data import (
    CSVFile,
    File,
    ForeignKeyValidator,
    JSONFile,
    OptionalColumnGuard,
    SimpleETLFactory,
    ValidationSequence,
    ValidationSeverity,
    XLSXFile,
)
from algomancy_data.extractor import (
    CSVSingleExtractor,
    ExtractionSequence,
    JSONSingleExtractor,
    XLSXMultiExtractor,
    XLSXSingleExtractor,
)
from algomancy_data.transformer import CleanTransformer, TransformationSequence

F = TypeVar("F", bound=File)


class ExampleETLFactory(SimpleETLFactory):
    """ETL factory for the bundled example data."""

    def create_extraction_sequence(
        self,
        files: Dict[str, F],
    ) -> ExtractionSequence:
        """Custom extraction because of non-default CSV separator + sheet selection.

        For schemas with no custom needs you would simply inherit the
        registry-driven default from :class:`ETLFactory`.
        """
        sequence = ExtractionSequence(logger=self.logger)

        sequence.add_extractor(
            CSVSingleExtractor(
                file=cast(CSVFile, files["sku_data"]),
                schema=self.get_schema("sku_data"),
                logger=self.logger,
                separator=";",
            )
        )
        sequence.add_extractor(
            CSVSingleExtractor(
                file=cast(CSVFile, files["warehouse_layout"]),
                schema=self.get_schema("warehouse_layout"),
                logger=self.logger,
                separator=";",
            )
        )
        sequence.add_extractor(
            JSONSingleExtractor(
                file=cast(JSONFile, files["employees"]),
                schema=self.get_schema("employees"),
                logger=self.logger,
            )
        )
        sequence.add_extractor(
            XLSXSingleExtractor(
                file=cast(XLSXFile, files["inventory"]),
                schema=self.get_schema("inventory"),
                sheet_name=1,
                logger=self.logger,
            )
        )
        sequence.add_extractor(
            XLSXMultiExtractor(
                file=cast(XLSXFile, files["multisheet"]),
                schema=self.get_schema("multisheet"),
                logger=self.logger,
            )
        )
        return sequence

    def create_validation_sequence(self) -> ValidationSequence:
        """Default validators (Required/Schema/PK) + cross-table integrity.

        Adding a ``ForeignKeyValidator`` makes sure every SKU referenced
        by a warehouse slot exists in the SKU table. ``OptionalColumnGuard``
        materialises any missing optional column using its declared
        ``Column.default`` so downstream code can rely on it.
        """
        sequence = super().create_validation_sequence()
        sequence.add_validator(OptionalColumnGuard(self.schemas))
        sequence.add_validator(
            ForeignKeyValidator(
                left_table="warehouse_layout",
                left_col="slotid",
                right_table="sku_data",
                right_col="currentslot",
                severity=ValidationSeverity.WARNING,
            )
        )
        return sequence

    def create_transformation_sequence(self) -> TransformationSequence:
        sequence = TransformationSequence(logger=self.logger)
        sequence.add_transformer(CleanTransformer(self.logger))
        return sequence
