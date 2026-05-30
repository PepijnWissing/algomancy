"""
Data inference utilities for detecting file types and inferring schemas.
"""

import pandas as pd
import re
from pathlib import Path
from typing import Dict, List
import warnings
import click

from algomancy_data import DataType, FileExtension


def _to_pascal_case(text: str) -> str:
    """Convert ``text`` to PascalCase, splitting on whitespace and non-alphanumerics."""
    parts = [p for p in re.split(r"[^0-9a-zA-Z]+", text) if p]
    return "".join(p[:1].upper() + p[1:] for p in parts)


def _to_snake_case(text: str) -> str:
    """Convert ``text`` to snake_case."""
    parts = [p for p in re.split(r"[^0-9a-zA-Z]+", text) if p]
    return "_".join(p.lower() for p in parts)


class DataFileInfo:
    """Information about a detected data file."""

    def __init__(
        self,
        file_path: Path,
        file_name: str,
        extension: FileExtension,
        sheet_names: List[str] = None,
    ):
        self.file_path = file_path
        self.file_name = file_name
        self.extension = extension
        self.sheet_names = sheet_names or []
        self.inferred_schemas: Dict[str, Dict[str, DataType]] = {}
        # Per-schema (per-sheet for MULTI, "default" for SINGLE) primary-key
        # candidates inferred from sample data. Consumed by the schema
        # template to emit ``primary_key=True`` on the right columns.
        self.primary_key_columns: Dict[str, List[str]] = {}

        # User configuration
        self.csv_separator: str = ","  # Default separator
        self.selected_sheets: List[str] = []  # For Excel files
        self.skip_file: bool = False  # User can choose to skip a file

        # Template-rendering metadata derived from file_name. Set here so the
        # schema template always renders a distinct class name even if later
        # steps (inference, metadata enrichment) are skipped or fail.
        self.class_name: str = _to_pascal_case(file_name) or "Data"
        self.snake_name: str = _to_snake_case(file_name) or "data"
        self.total_columns: int = 0

    @property
    def is_multi_sheet(self) -> bool:
        """Check if this file contains multiple sheets to be extracted."""
        return len(self.selected_sheets) > 1

    @property
    def sheets_to_extract(self) -> List[str]:
        """Get list of sheets that should be extracted (for Excel files)."""
        return self.selected_sheets if self.selected_sheets else self.sheet_names


class SchemaInferenceEngine:
    """Engine for inferring data schemas from files."""

    # Mapping from file extensions to FileExtension enum
    EXTENSION_MAP = {
        ".csv": FileExtension.CSV,
        ".xlsx": FileExtension.XLSX,
        ".json": FileExtension.JSON,
    }

    def __init__(self, sample_rows: int = 100):
        self.sample_rows = sample_rows

    def scan_directory(self, directory: Path) -> List[DataFileInfo]:
        """
        Scan a directory for supported data files.

        Args:
            directory: Path to scan for data files.

        Returns:
            List of DataFileInfo objects for detected files.
        """
        files = []

        if not directory.exists():
            return files

        for file_path in directory.iterdir():
            if not file_path.is_file():
                continue

            extension = self._get_file_extension(file_path)
            if extension is None:
                continue

            file_info = DataFileInfo(
                file_path=file_path, file_name=file_path.stem, extension=extension
            )

            # For Excel files, detect sheet names
            if extension == FileExtension.XLSX:
                file_info.sheet_names = self._get_excel_sheets(file_path)

            files.append(file_info)

        return files

    def infer_schema_interactive(self, file_info: DataFileInfo) -> bool:
        """
        Interactively infer schema from a data file with user input.

        Prompts user for configuration (CSV separator, Excel sheets) before
        inferring the schema.

        Args:
            file_info: DataFileInfo object to infer schema for.

        Returns:
            True if schema was successfully inferred, False if skipped or failed.
        """
        click.echo()
        click.echo(
            click.style(
                f"━━━ Processing: {file_info.file_name}{file_info.file_path.suffix} ━━━",
                fg="cyan",
                bold=True,
            )
        )
        click.echo()

        # Ask if user wants to process this file
        if not click.confirm(
            "Do you want to include this file in your ETL pipeline?", default=True
        ):
            file_info.skip_file = True
            click.echo(click.style("  ⊘ Skipping file", fg="yellow"))
            return False

        # Get file-specific configuration
        if file_info.extension == FileExtension.CSV:
            self._configure_csv(file_info)
        elif file_info.extension == FileExtension.XLSX:
            self._configure_excel(file_info)

        # Infer schema with user configuration
        return self._infer_schema_with_config(file_info)

    def _configure_csv(self, file_info: DataFileInfo):
        """
        Ask user for CSV-specific configuration.

        Args:
            file_info: DataFileInfo for a CSV file.
        """
        click.echo("CSV Configuration:")

        # Try to detect separator by reading first few lines
        detected_sep = self._detect_csv_separator(file_info.file_path)

        if detected_sep:
            click.echo(f"  Detected separator: '{detected_sep}'")
            default_sep = detected_sep
        else:
            click.echo("  Could not auto-detect separator")
            default_sep = ","

        separator = click.prompt("  Enter CSV separator", default=default_sep, type=str)

        file_info.csv_separator = separator
        click.echo()

    def _configure_excel(self, file_info: DataFileInfo):
        """
        Ask user which Excel sheets to extract.

        Args:
            file_info: DataFileInfo for an Excel file.
        """
        if not file_info.sheet_names:
            click.echo(click.style("    No sheets detected in Excel file", fg="yellow"))
            return

        click.echo(f"Excel file contains {len(file_info.sheet_names)} sheet(s):")
        for i, sheet in enumerate(file_info.sheet_names, 1):
            click.echo(f"  {i}. {sheet}")
        click.echo()

        if len(file_info.sheet_names) == 1:
            # Only one sheet, use it by default
            file_info.selected_sheets = file_info.sheet_names
            click.echo(f"  → Using single sheet: {file_info.sheet_names[0]}")
        else:
            # Multiple sheets, ask user
            choice = click.prompt(
                "Extract all sheets or select specific ones?",
                type=click.Choice(["all", "select"], case_sensitive=False),
                default="all",
            )

            if choice == "all":
                file_info.selected_sheets = file_info.sheet_names
                click.echo(f"  → Extracting all {len(file_info.sheet_names)} sheets")
            else:
                # Let user select sheets
                click.echo()
                click.echo(
                    "Enter sheet numbers to extract (comma-separated, e.g., '1,3' or '1-3'):"
                )
                selected = click.prompt("  Sheets", type=str, default="1")

                file_info.selected_sheets = self._parse_sheet_selection(
                    selected, file_info.sheet_names
                )

                if file_info.selected_sheets:
                    click.echo(
                        f"  → Selected sheets: {', '.join(file_info.selected_sheets)}"
                    )
                else:
                    click.echo(
                        click.style(
                            "    No valid sheets selected, using all", fg="yellow"
                        )
                    )
                    file_info.selected_sheets = file_info.sheet_names

        click.echo()

    def _parse_sheet_selection(
        self, selection: str, sheet_names: List[str]
    ) -> List[str]:
        """
        Parse user sheet selection string into list of sheet names.

        Supports:
        - Individual numbers: "1,3,5"
        - Ranges: "1-3"
        - Mixed: "1,3-5,7"

        Args:
            selection: User input string
            sheet_names: List of available sheet names

        Returns:
            List of selected sheet names
        """
        selected_sheets = []

        try:
            # Split by comma
            parts = selection.split(",")

            for part in parts:
                part = part.strip()

                if "-" in part:
                    # Range
                    start, end = part.split("-")
                    start_idx = int(start.strip()) - 1
                    end_idx = int(end.strip()) - 1

                    for i in range(start_idx, end_idx + 1):
                        if 0 <= i < len(sheet_names):
                            selected_sheets.append(sheet_names[i])
                else:
                    # Single number
                    idx = int(part) - 1
                    if 0 <= idx < len(sheet_names):
                        selected_sheets.append(sheet_names[idx])

            # Remove duplicates while preserving order
            seen = set()
            unique_sheets = []
            for sheet in selected_sheets:
                if sheet not in seen:
                    seen.add(sheet)
                    unique_sheets.append(sheet)

            return unique_sheets

        except (ValueError, IndexError):
            return []

    def _detect_csv_separator(self, file_path: Path) -> str | None:
        """
        Try to detect CSV separator by reading first few lines.

        Args:
            file_path: Path to CSV file.

        Returns:
            Detected separator or None if detection failed.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                # Read first 5 lines
                lines = [f.readline() for _ in range(5)]

            # Count common separators
            separators = [",", ";", "\t", "|"]
            counts = {}

            for sep in separators:
                # Count occurrences in each line
                line_counts = [line.count(sep) for line in lines if line.strip()]

                # If separator appears consistently across lines, it's likely correct
                if line_counts and len(set(line_counts)) == 1 and line_counts[0] > 0:
                    counts[sep] = line_counts[0]

            # Return separator with highest count
            if counts:
                return max(counts, key=counts.get)

            return None

        except Exception:
            return None

    def _infer_schema_with_config(self, file_info: DataFileInfo) -> bool:
        """
        Infer schema using user-provided configuration.

        Args:
            file_info: DataFileInfo with configuration set.

        Returns:
            True if successful, False otherwise.
        """
        try:
            if file_info.extension == FileExtension.CSV:
                df = pd.read_csv(
                    file_info.file_path,
                    nrows=self.sample_rows,
                    sep=file_info.csv_separator,
                )
                file_info.inferred_schemas["default"] = self._infer_from_dataframe(df)
                file_info.primary_key_columns["default"] = self._infer_primary_keys(df)
                click.echo(f"  ✓ Inferred schema with {len(df.columns)} columns")

            elif file_info.extension == FileExtension.XLSX:
                # Read selected sheets only
                for sheet_name in file_info.sheets_to_extract:
                    df = pd.read_excel(
                        file_info.file_path,
                        sheet_name=sheet_name,
                        nrows=self.sample_rows,
                    )
                    file_info.inferred_schemas[sheet_name] = self._infer_from_dataframe(
                        df
                    )
                    file_info.primary_key_columns[sheet_name] = (
                        self._infer_primary_keys(df)
                    )
                    click.echo(f"  ✓ Sheet '{sheet_name}': {len(df.columns)} columns")

            elif file_info.extension == FileExtension.JSON:
                # Use json_normalize to flatten nested structures
                import json

                with open(file_info.file_path, "r") as f:
                    json_data = json.load(f)

                # Normalize JSON to flatten nested objects
                df = pd.json_normalize(json_data)

                if len(df) > self.sample_rows:
                    df = df.head(self.sample_rows)

                file_info.inferred_schemas["default"] = self._infer_from_dataframe(df)
                file_info.primary_key_columns["default"] = self._infer_primary_keys(df)
                click.echo(f"  ✓ Inferred schema with {len(df.columns)} columns")

            return True

        except Exception as e:
            click.echo(click.style(f"   Error inferring schema: {e}", fg="red"))
            return False

    def _infer_from_dataframe(self, df: pd.DataFrame) -> Dict[str, DataType]:
        """
        Infer data types from a pandas DataFrame.

        Args:
            df: DataFrame to infer types from.

        Returns:
            Dictionary mapping column names to DataType enum values.
        """
        schema = {}

        for column in df.columns:
            dtype = df[column].dtype

            # Infer DataType from pandas dtype
            if pd.api.types.is_integer_dtype(dtype):
                schema[column] = DataType.INTEGER
            elif pd.api.types.is_float_dtype(dtype):
                schema[column] = DataType.FLOAT
            elif pd.api.types.is_bool_dtype(dtype):
                schema[column] = DataType.BOOLEAN
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                schema[column] = DataType.DATETIME
            elif pd.api.types.is_string_dtype(dtype) or pd.api.types.is_object_dtype(
                dtype
            ):
                # Check if column contains nested structures (lists or dicts)
                if self._contains_nested_structures(df[column]):
                    # For nested structures, treat as STRING
                    # (will be converted to JSON string during extraction)
                    schema[column] = DataType.STRING
                # Try to detect if it's actually a date
                elif self._looks_like_datetime(df[column]):
                    schema[column] = DataType.DATETIME
                else:
                    schema[column] = DataType.STRING
            else:
                # Default to STRING for unknown types
                schema[column] = DataType.STRING

        return schema

    def _infer_primary_keys(self, df: pd.DataFrame) -> List[str]:
        """Heuristically pick primary-key columns from sample data.

        A column is treated as PK-like when it is all-unique, all-non-null,
        and either named ``id`` / ``*_id`` or is the single best unique
        column in the sample. Returns at most one column to avoid emitting
        compound PKs that the user didn't actually ask for.
        """
        if df.empty:
            return []

        candidates: List[str] = []
        for column in df.columns:
            series = df[column]
            if series.isna().any():
                continue
            if series.nunique() != len(series):
                continue
            lowered = str(column).lower()
            if lowered == "id" or lowered.endswith("_id") or lowered.endswith("id"):
                candidates.append(column)

        return candidates[:1]

    def _contains_nested_structures(self, series: pd.Series) -> bool:
        """
        Check if a series contains nested structures (lists or dicts).

        Args:
            series: Pandas series to check.

        Returns:
            True if the series contains lists or dictionaries.
        """
        if len(series) == 0:
            return False

        # Sample a few non-null values
        sample = series.dropna().head(5)
        if len(sample) == 0:
            return False

        # Check if any sampled value is a list or dict
        for value in sample:
            if isinstance(value, (list, dict)):
                return True

        return False

    def _looks_like_datetime(self, series: pd.Series) -> bool:
        """
        Check if a series looks like it contains datetime values.

        Args:
            series: Pandas series to check.

        Returns:
            True if the series appears to contain datetime values.
        """
        if len(series) == 0:
            return False

        # Sample a few non-null values
        sample = series.dropna().head(5)
        if len(sample) == 0:
            return False

        # Try to parse as datetime
        try:
            # Suppress the UserWarning about format inference
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                pd.to_datetime(sample)
            return True
        except (ValueError, TypeError):
            return False

    def _get_file_extension(self, file_path: Path) -> FileExtension | None:
        """
        Get FileExtension enum for a file path.

        Args:
            file_path: Path to check.

        Returns:
            FileExtension enum value or None if not supported.
        """
        suffix = file_path.suffix.lower()
        return self.EXTENSION_MAP.get(suffix)

    def _get_excel_sheets(self, file_path: Path) -> List[str]:
        """
        Get list of sheet names from an Excel file.

        Args:
            file_path: Path to Excel file.

        Returns:
            List of sheet names.
        """
        try:
            excel_file = pd.ExcelFile(file_path)
            return excel_file.sheet_names
        except Exception:
            return []
