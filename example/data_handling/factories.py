"""ETL factory for the example app.

Demonstrates the M4 boilerplate reductions in ``algomancy_data``:

* ``create_loader`` is not overridden — the inherited default
  (``DataSourceLoader``) is used.
* ``create_validation_sequence`` calls ``super()`` to inherit
  ``RequiredColumnsValidator + SchemaValidator + PrimaryKeyValidator``
  (the PK validator is added automatically because some schemas declare
  a primary key) and only adds the dataset-specific
  ``MissingValueValidator`` and ``UniqueValueValidator``.
* ``create_extraction_sequence`` defers to the registry for files that
  work with default extractor constructor args and only hand-wires the
  files that need non-default parameters (CSV separator, XLSX sheet
  index).
"""

from typing import Dict, TypeVar, cast

from algomancy_data import (
    CSVFile,
    ETLFactory,
    File,
    MissingValueValidator,
    OptionalColumnGuard,
    UniqueValueValidator,
    ValidationSequence,
    ValidationSeverity,
    XLSXFile,
)
from algomancy_data.extractor import (
    CSVSingleExtractor,
    ExtractionSequence,
    XLSXSingleExtractor,
)
from algomancy_data.transformer import (
    CascadeDropTransformer,
    CleanTransformer,
    TransformationSequence,
)

F = TypeVar("F", bound=File)


class ExampleETLFactory(ETLFactory):
    """Showcases the M4 boilerplate reductions.

    Inherits the default loader and the default schema / required-column /
    primary-key validators. Only customises the bits that the example
    data actually needs.
    """

    def create_extraction_sequence(
        self,
        files: Dict[str, F],
    ) -> ExtractionSequence:
        # Files that work with the registry's default extractors —
        # ``super()`` builds them straight from each schema's
        # ``(extension, schema_type)`` pair.
        default_files = {
            name: files[name] for name in ("employees", "multisheet") if name in files
        }
        sequence = super().create_extraction_sequence(default_files)

        # Parent/child demo files for the cascade-drop showcase.
        for name in ("categories", "products", "order_items"):
            if name in files:
                sequence.add_extractor(
                    CSVSingleExtractor(
                        file=cast(CSVFile, files[name]),
                        schema=self.get_schema(name),
                        separator=";",
                        logger=self.logger,
                    )
                )

        # Files that need non-default extractor params (custom separator,
        # explicit sheet index) — still wired by hand.
        sequence.add_extractor(
            CSVSingleExtractor(
                file=cast(CSVFile, files["sku_data"]),
                schema=self.get_schema("sku_data"),
                separator=";",
                logger=self.logger,
            )
        )
        sequence.add_extractor(
            CSVSingleExtractor(
                file=cast(CSVFile, files["warehouse_layout"]),
                schema=self.get_schema("warehouse_layout"),
                separator=";",
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
        return sequence

    def create_validation_sequence(self) -> ValidationSequence:
        sequence = super().create_validation_sequence()
        sequence.add_validator(
            MissingValueValidator(
                table="employees",
                columns=["name", "email", "is_active"],
                severity=ValidationSeverity.ERROR,
            )
        )
        sequence.add_validator(
            UniqueValueValidator(
                table="employees",
                columns=["email"],
                severity=ValidationSeverity.WARNING,
            )
        )
        return sequence

    def create_transformation_sequence(self) -> TransformationSequence:
        sequence = TransformationSequence(logger=self.logger)
        sequence.add_transformer(
            OptionalColumnGuard(schemas=self.schemas, logger=self.logger)
        )
        sequence.add_transformer(CleanTransformer(self.logger))
        sequence.add_transformer(
            CascadeDropTransformer(schemas=self.schemas, logger=self.logger)
        )
        return sequence
