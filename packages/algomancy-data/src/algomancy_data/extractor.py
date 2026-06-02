from abc import ABC, abstractmethod
from io import StringIO
from typing import Dict, List, Optional

import pandas as pd
import json

from .schema import Schema, DataType
from .file import File, XLSXFile, JSONFile, CSVFile
from algomancy_utils import Logger


class DateFormatError(Exception):
    pass


class ConversionIssue:
    """Single dtype-conversion failure surfaced by ``DataTypeConverter``."""

    __slots__ = ("table", "column", "target_type", "reason")

    def __init__(
        self, table: str, column: str, target_type: DataType, reason: str
    ) -> None:
        #: Logical table/file name where the failure occurred.
        self.table = table
        #: Column whose conversion failed.
        self.column = column
        #: The schema-declared target ``DataType``.
        self.target_type = target_type
        #: Short description of the failure.
        self.reason = reason

    def __repr__(self) -> str:
        return (
            f"ConversionIssue(table={self.table!r}, column={self.column!r}, "
            f"target_type={self.target_type!r}, reason={self.reason!r})"
        )


class DataTypeConverter:
    @staticmethod
    def convert_dtypes(
        df: pd.DataFrame,
        schema_types: dict[str, DataType],
        issues: Optional[List[ConversionIssue]] = None,
        table_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Converts DataFrame columns to the specified data types in the schema.
        Attempts different localization options for numeric columns and date formats if the initial conversion fails.

        Args:
            df: The pandas DataFrame to convert.
            schema_types: dictionary containing target_types for data, obtained
                from schema.
            issues: Optional list that receives ``ConversionIssue`` entries for
                any column that fails to convert. The caller (typically an
                extractor) is expected to surface these via the validation
                step rather than silently corrupting data.
            table_name: Optional logical table name used to attach context to
                ``ConversionIssue`` entries.

        Returns:
            DataFrame with converted data types where possible.
        """

        result_df = df.copy()

        for column, target_type in schema_types.items():
            if column not in result_df.columns:
                continue

            if target_type in (DataType.FLOAT, DataType.INTEGER):
                result_df = DataTypeConverter._convert_numeric_column(
                    result_df, column, target_type, issues, table_name
                )
            elif target_type == DataType.DATETIME:
                result_df = DataTypeConverter._convert_datetime_column(
                    result_df, column, issues, table_name
                )
            elif target_type == DataType.BOOLEAN:
                result_df = DataTypeConverter._convert_boolean_column(
                    result_df, column, issues, table_name
                )
            elif target_type == DataType.STRING:
                result_df = DataTypeConverter._convert_string_column(
                    result_df, column, issues, table_name
                )
            else:
                raise NotImplementedError(f"Unsupported data type: {target_type}")

        return result_df

    @staticmethod
    def _convert_numeric_column(
        df: pd.DataFrame,
        column: str,
        target_type: DataType,
        issues: Optional[List[ConversionIssue]] = None,
        table_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """Convert a column to a numeric type, handling different number formats."""
        try:
            # Standard conversion first
            df[column] = df[column].astype(target_type)
        except (ValueError, TypeError):
            # Try fixing common localization issues
            try:
                # Try European format (comma as decimal separator)
                if df[column].dtype == "object" and len(df[column]) > 0:
                    if target_type == DataType.FLOAT:
                        temp_values = (
                            df[column].str.replace(",", ".").astype(DataType.FLOAT)
                        )
                        df[column] = temp_values
                    else:
                        # For integers, first convert to float (handling comma separators) then to int
                        temp_values = (
                            df[column]
                            .str.replace(",", ".")
                            .astype(DataType.FLOAT)
                            .astype(DataType.INTEGER)
                        )
                        df[column] = temp_values
            except (ValueError, TypeError, AttributeError, IndexError):
                try:
                    # Try with thousands separator removal
                    if df[column].dtype == "object" and len(df[column]) > 0:
                        if target_type == DataType.FLOAT:
                            temp_values = (
                                df[column].str.replace(",", "").astype(DataType.FLOAT)
                            )
                            df[column] = temp_values
                        else:
                            temp_values = (
                                df[column].str.replace(",", "").astype(DataType.INTEGER)
                            )
                            df[column] = temp_values
                except (ValueError, TypeError, AttributeError, IndexError) as exc:
                    if issues is not None:
                        issues.append(
                            ConversionIssue(
                                table=table_name or "",
                                column=column,
                                target_type=target_type,
                                reason=f"Numeric conversion failed: {exc}",
                            )
                        )
        return df

    @staticmethod
    def _convert_date_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Convert a column to date type, trying multiple formats."""
        try:
            # Standard conversion using pandas to_datetime
            temp = pd.to_datetime(df[column])
            df[column] = temp
        except (ValueError, TypeError, AttributeError):
            # Try different date formats
            success = False
            for date_format in [
                "%Y-%m-%d",
                "%m/%d/%Y",
                "%d/%m/%Y",
                "%d-%m-%Y",
                "%d.%m.%Y",
            ]:
                try:
                    temp = pd.to_datetime(df[column], format=date_format)
                    df[column] = temp
                    success = True
                    break  # Break the loop if conversion succeeds
                except (ValueError, TypeError, AttributeError):
                    continue  # Try next format
            if not success:
                raise DateFormatError(
                    f"Could not convert column '{column}' to date format."
                )
        return df

    @staticmethod
    def _convert_datetime_column(
        df: pd.DataFrame,
        column: str,
        issues: Optional[List[ConversionIssue]] = None,
        table_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """Convert a column to datetime type, trying multiple formats."""
        try:
            DataTypeConverter._convert_date_column(df, column)
        except DateFormatError:
            # try to format as datetime
            pass

        try:
            # Standard conversion using pandas to_datetime
            temp = pd.to_datetime(df[column])
            df[column] = temp
            return df
        except (ValueError, TypeError):
            # Try different datetime formats
            for datetime_format in [
                "%Y-%m-%d %H:%M:%S",
                "%m/%d/%Y %H:%M:%S",
                "%d/%m/%Y %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%d.%m.%Y %H:%M:%S",
            ]:
                try:
                    temp = pd.to_datetime(df[column], format=datetime_format)
                    df[column] = temp
                    return df
                except (ValueError, TypeError, AttributeError):
                    continue  # Try next format
            if issues is not None:
                issues.append(
                    ConversionIssue(
                        table=table_name or "",
                        column=column,
                        target_type=DataType.DATETIME,
                        reason="Could not parse column as datetime in any known format.",
                    )
                )
        return df

    @staticmethod
    def _convert_boolean_column(
        df: pd.DataFrame,
        column: str,
        issues: Optional[List[ConversionIssue]] = None,
        table_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """Convert a column to boolean type, handling various representations."""
        try:
            df[column] = df[column].astype(DataType.BOOLEAN)
        except (ValueError, TypeError):
            try:
                # Try common boolean string representations
                bool_map = {
                    "true": True,
                    "yes": True,
                    "y": True,
                    "1": True,
                    "t": True,
                    "false": False,
                    "no": False,
                    "n": False,
                    "0": False,
                    "f": False,
                }

                if df[column].dtype == "object":  # Only apply for string types
                    temp = df[column].astype(str).str.lower().map(bool_map)
                    # Only update if mapping was successful (not NaN)
                    mask = ~temp.isna()
                    if mask.any():
                        df.loc[mask, column] = temp[mask]
                        # Try to convert the whole column to bool if all values were mapped
                        if mask.all():
                            df[column] = df[column].astype(DataType.BOOLEAN)
            except (ValueError, TypeError, AttributeError) as exc:
                if issues is not None:
                    issues.append(
                        ConversionIssue(
                            table=table_name or "",
                            column=column,
                            target_type=DataType.BOOLEAN,
                            reason=f"Boolean conversion failed: {exc}",
                        )
                    )
        return df

    @staticmethod
    def _convert_string_column(
        df: pd.DataFrame,
        column: str,
        issues: Optional[List[ConversionIssue]] = None,
        table_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """Convert a column to other non-specialized types."""
        try:
            # Update the column in the original dataframe with the target type
            df[column] = df[column].astype(DataType.STRING)
        except (ValueError, TypeError) as exc:
            if issues is not None:
                issues.append(
                    ConversionIssue(
                        table=table_name or "",
                        column=column,
                        target_type=DataType.STRING,
                        reason=f"String conversion failed: {exc}",
                    )
                )
        return df


class Extractor(ABC):
    def __init__(self, file: File, logger: Logger = None) -> None:
        self.file = file
        self.logger = logger
        # Buffer for dtype conversion failures detected during extract().
        # The owning ExtractionSequence drains this list after each extractor
        # runs so the validation step can surface them as messages.
        self.conversion_issues: List[ConversionIssue] = []

    def _extraction_message(self):
        if self.logger:
            self.logger.log(f"Extracting from {self.file.name}")

    def _extraction_success_message(self):
        if self.logger:
            self.logger.success(f"Extraction of {self.file.name} successful")

    @abstractmethod
    def extract(self) -> Dict[str, pd.DataFrame]:
        pass


class SingleExtractor(Extractor):
    def __init__(self, file: File, schema: Schema, logger: Logger = None) -> None:
        super().__init__(file, logger)
        self.schema = schema

    def extract(self) -> Dict[str, pd.DataFrame]:
        """Returns Dict[name, dataframe], so each dataset is identifiable"""

        self._extraction_message()
        df = self._extract_file()
        df = DataTypeConverter.convert_dtypes(
            df,
            self.schema.datatypes(),
            issues=self.conversion_issues,
            table_name=self.file.name,
        )
        self._extraction_success_message()

        return {self.file.name: df}

    @abstractmethod
    def _extract_file(self) -> pd.DataFrame:
        """

        Returns:
        :raises FileNotFoundError: handled one level higher
        """
        pass


class MultiExtractor(Extractor):
    def __init__(self, files: File, schema: Schema, logger: Logger = None) -> None:
        super().__init__(files, logger)
        assert schema.is_multi(), (
            f"MultiExtractor for {schema.file_name()} requires a multi-schema"
        )
        self.schema = schema

    def _check_schemas(self, dfs: Dict[str, pd.DataFrame]):
        missing_keys = set(dfs.keys()) - set(
            [
                self.get_extraction_key(name)
                for name in self.schema.datatype_groups().keys()
            ]
        )
        assert len(missing_keys) == 0, f"Missing schemas for keys: {missing_keys}"

    def _get_schema_types(self, key) -> Dict[str, DataType]:
        return self.schema.datatype_groups()[key]

    def extract(self) -> Dict[str, pd.DataFrame]:
        """Returns Dict[name, dataframe], so each dataset is identifiable"""

        self._extraction_message()

        dfs = self._extract_files()

        # Attemting to convert all dataframes with the corresponing schema
        # Before this we check if the keys of the schemas and the names of the extracted dataframes match
        self._check_schemas(dfs)
        dfs = {
            key: DataTypeConverter.convert_dtypes(
                df,
                self._get_schema_types(self.get_schema_name(key)),
                issues=self.conversion_issues,
                table_name=key,
            )
            for key, df in dfs.items()
        }

        self._extraction_success_message()
        return dfs

    def get_extraction_key(self, name: str) -> str:
        return f"{self.file.name}.{name}"

    def get_schema_name(self, extraction_key: str) -> str:
        prefix = f"{self.file.name}."
        if extraction_key.startswith(prefix):
            return extraction_key[len(prefix) :]
        return extraction_key

    @abstractmethod
    def _extract_files(self) -> Dict[str, pd.DataFrame]:
        """

        Returns:
        :raises FileNotFoundError: handled one level higher
        """
        pass


class CSVSingleExtractor(SingleExtractor):
    """
    Parses and extracts data from a CSV file.

    This class is designed for reading and extracting data specifically
    from Comma-Separated Values (CSV) files. It uses pandas for
    data manipulation and allows customization of the delimiter used
    in the CSV file through the separator parameter. The extracted data
    is provided in the form of a pandas DataFrame.

    Attributes:
        file: CSVFile
            File object that contains the content of the CSV file.
        schema: Schema
            contains datatype information for each column in the DataFrame.
        logger: Logger, optional
            An optional logger instance to log messages and errors.
        separator: str
            The delimiter string to use for parsing the CSV file
            (default is ";").
    """

    def __init__(
        self, file: CSVFile, schema: Schema, logger: Logger = None, separator: str = ";"
    ) -> None:
        super().__init__(file, schema, logger)
        self._separator = separator

    def _extract_file(self) -> pd.DataFrame:
        csv_content = self.file.content
        df = pd.read_csv(StringIO(csv_content), sep=self._separator)
        return df


class JSONSingleExtractor(SingleExtractor):
    """
    Handles extraction of data from JSON files.

    This class is designed to read and process data from a JSON file.
    It normalizes the JSON structure and converts it into a pandas DataFrame
    for further processing. It inherits from the Extractor base class and
    uses similar initialization parameters such as a file path and an
    optional logger.

    JSONSingleExtractor expects the JSON file to be formatted such that the root level is
    a list. Each item in the list represents a single record, and each record has
    some properties. The properties are represented as key-value pairs. If the value
    is a dictionary, it is treated as a nested object. Each nested object is converted
    to a column in the dataframe. If the value is a list, it is converted to a string.

    Attributes:
        file: JSONFile
            File object that contains the content of the JSON file.
        schema: Schema
            contains datatype information for each column in the DataFrame.
        logger: Logger, optional
            Logger instance for logging messages. Defaults to None.
    """

    def __init__(self, file: JSONFile, schema: Schema, logger: Logger = None) -> None:
        super().__init__(file, schema, logger)

    def _extract_file(self) -> pd.DataFrame:
        json_data = json.load(StringIO(self.file.content))
        df = pd.json_normalize(json_data)

        return df


class XLSXSingleExtractor(SingleExtractor):
    """
    Represents an extractor for XLSX files.

    This class is designed to handle the extraction of data from XLSX files.
    It uses pandas to read specified sheets from an XLSX file and converts
    the content into a DataFrame. It extends the functionality of a base
    SingleExtractor class, providing a specialized implementation for XLSX data.

    Attributes:
        file: XLSXFile
            The file object containing the content of the XLSX file.
        schema: Schema
            The schema object containing the data types for each column in the DataFrame.
        sheet_name: str | int
            The name or index of the sheet to extract data from.
        logger: Logger, optional
            An optional logger instance for logging purposes.
    """

    def __init__(
        self,
        file: XLSXFile,
        schema: Schema,
        sheet_name: str | int,
        logger: Logger = None,
    ) -> None:
        super().__init__(file, schema, logger)
        self._sheet_name: str | int = sheet_name

    def _extract_file(self) -> pd.DataFrame:
        # Parse the content stored in the file
        content_obj = json.loads(self.file.content)

        # Handle sheet selection
        sheet_name = self._sheet_name

        # If sheet_name is an integer, convert it to the actual sheet name using the mapping
        if isinstance(sheet_name, int):
            # Get the sheet name from the index mapping
            if str(sheet_name) in content_obj["metadata"]["index_to_sheet_name"]:
                sheet_name = content_obj["metadata"]["index_to_sheet_name"][
                    str(sheet_name)
                ]
            else:
                # Use the index directly to get from the list of sheet names
                try:
                    sheet_name = content_obj["metadata"]["sheet_names"][sheet_name]
                except IndexError:
                    raise ValueError(
                        f"Sheet index {sheet_name} is out of range. "
                        f"Available sheets: {content_obj['metadata']['sheet_names']}"
                    )

        # Check if the requested sheet exists
        if sheet_name not in content_obj["sheets"]:
            raise ValueError(
                f"Sheet '{sheet_name}' not found in Excel file. "
                f"Available sheets: {content_obj['metadata']['sheet_names']}"
            )

        # Get the data for the requested sheet
        sheet_data = content_obj["sheets"][sheet_name]

        # Convert back to DataFrame
        df = pd.DataFrame(sheet_data)

        return df


class XLSXMultiExtractor(MultiExtractor):
    """
    Represents an extractor for XLSX files.

    This class is designed to handle the extraction of data from XLSX files.
    It uses pandas to read specified sheets from an XLSX file and converts
    the content into DataFrame(s). It extends the functionality of a base
    MultiExtractor class, providing a specialized implementation for XLSX data.

    Attributes:
        file: XLSXFile
            The file object containing the content of the XLSX file.
        schemas: Schema
            The schema object containing the data types for each column in the DataFrame.
        sheet_names: List[str]
            The name of the sheets to extract data from.
        logger: Logger, optional
            An optional logger instance for logging purposes.

    Note that the sheet_names should match the keys of the schemas Dict.
    """

    def __init__(
        self,
        file: XLSXFile,
        schema: Schema,
        logger: Logger = None,
    ) -> None:
        super().__init__(file, schema, logger)
        self._sheet_names = list(self.schema.sub_names())
        self._single_sheet_extractors = {}
        for sheet_name in self._sheet_names:
            subschema = self.schema.get_subschema(sheet_name)
            self._single_sheet_extractors[sheet_name] = XLSXSingleExtractor(
                file, subschema, sheet_name
            )

    def _extract_files(self) -> Dict[str, pd.DataFrame]:
        dfs = {}
        for name, extractor in self._single_sheet_extractors.items():
            dfs[self.get_extraction_key(name)] = list(extractor.extract().values())[0]
        return dfs


class JSONMultiExtractor(MultiExtractor):
    """Extract a nested JSON document into multiple related tables.

    The schema must be a ``SchemaType.MULTI`` schema declaring one
    :class:`~algomancy_data.schema.ColumnGroup` per output table. Each group's
    ``source_path`` says where its rows live relative to a root record:

    - ``source_path=()`` — the **root** group. Each item of the top-level list
      contributes one row. Exactly one group must use this.
    - ``source_path=("PickOrderLines",)`` — a **child** group. Each root
      record has a nested list at that key whose elements become this group's
      rows. Deeper paths (``("foo", "bar")``) walk through intermediate dicts
      before reaching the list.

    A child column whose ``foreign_key=(parent_group_name, parent_pk_column)``
    is automatically populated from the corresponding root record at extraction
    time. The same FK declaration is also consumed by
    :class:`~algomancy_data.validator.ForeignKeyValidator` and
    :class:`~algomancy_data.transformer.CascadeDropTransformer`.

    The top-level JSON may be either a list of records, or a dict with exactly
    one list-valued key (the wrapper is unwrapped automatically). List columns
    that are peeled off into a child group are dropped from the parent table so
    each row is a flat, queryable record.

    Attributes:
        file: ``JSONFile`` containing the nested document.
        schema: ``MULTI`` schema whose ``ColumnGroup``s carry the
            ``source_path`` and ``foreign_key`` metadata.
    """

    def __init__(
        self,
        file: JSONFile,
        schema: Schema,
        logger: Logger = None,
    ) -> None:
        super().__init__(file, schema, logger)
        # Resolve and cache group descriptors at construction time so
        # mistakes surface eagerly rather than at extract().
        self._groups = self._resolve_groups()
        root = [g for g in self._groups if not g["source_path"]]
        assert len(root) == 1, (
            f"JSONMultiExtractor for {schema.file_name()} requires exactly one "
            f"ColumnGroup with source_path=() (root/parent); found {len(root)}."
        )
        self._root = root[0]
        self._children = [g for g in self._groups if g["source_path"]]
        # FK targets on child groups must reference the root group's PK.
        for child in self._children:
            for col in child["columns"]:
                if col.foreign_key is None:
                    continue
                parent_table, parent_col = col.foreign_key
                if parent_table != self._root["name"]:
                    continue
                assert parent_col in self._root["pk_cols"] or any(
                    c.name == parent_col for c in self._root["columns"]
                ), (
                    f"Child group '{child['name']}' column '{col.name}' "
                    f"declares foreign_key to '{parent_table}.{parent_col}', "
                    f"but no such column exists on the root group."
                )

    def _resolve_groups(self) -> List[Dict]:
        """Return per-group descriptors: name, columns, source_path, pk_cols."""
        from .schema import ColumnGroup

        groups = [
            attr for attr in vars(self.schema).values() if isinstance(attr, ColumnGroup)
        ]
        assert groups, (
            f"JSONMultiExtractor requires {self.schema.file_name()} to declare "
            "ColumnGroup attributes (legacy _DATATYPES dicts are not supported "
            "for nested JSON because they cannot carry source_path)."
        )
        out: List[Dict] = []
        for grp in groups:
            pk_cols = tuple(c.name for c in grp.columns if c.primary_key)
            out.append(
                {
                    "name": grp.name,
                    "columns": list(grp.columns),
                    "source_path": tuple(grp.source_path),
                    "pk_cols": pk_cols,
                }
            )
        return out

    @staticmethod
    def _resolve_list(record: dict, path: tuple) -> list:
        """Walk ``path`` through ``record`` and return the list at the end.

        Returns ``[]`` when any intermediate hop is missing/``None`` or the
        final value is not a list. Non-strict because nested arrays are
        commonly optional in real-world JSON.
        """
        cur = record
        for key in path:
            if not isinstance(cur, dict):
                return []
            cur = cur.get(key)
            if cur is None:
                return []
        return cur if isinstance(cur, list) else []

    def _load_root_records(self) -> list:
        raw = json.load(StringIO(self.file.content))
        if isinstance(raw, list):
            return raw
        if isinstance(raw, dict):
            list_values = [v for v in raw.values() if isinstance(v, list)]
            if len(list_values) == 1:
                return list_values[0]
        raise ValueError(
            f"JSONMultiExtractor expects {self.file.name} to contain either a "
            "top-level list of records or a dict with exactly one list-valued "
            "key."
        )

    def _extract_files(self) -> Dict[str, pd.DataFrame]:
        root_records = self._load_root_records()

        parent_df = pd.json_normalize(root_records)
        # Drop columns that correspond to nested lists peeled off into
        # child tables. Dot-joined path matches how json_normalize names
        # intermediate dict expansions.
        for child in self._children:
            col_to_drop = ".".join(child["source_path"])
            if col_to_drop in parent_df.columns:
                parent_df = parent_df.drop(columns=[col_to_drop])

        child_dfs: Dict[str, pd.DataFrame] = {}
        for child in self._children:
            rows: List[dict] = []
            fk_specs = [
                (col.name, col.foreign_key[1])
                for col in child["columns"]
                if col.foreign_key and col.foreign_key[0] == self._root["name"]
            ]
            for record in root_records:
                if not isinstance(record, dict):
                    continue
                sublist = self._resolve_list(record, child["source_path"])
                for item in sublist:
                    if not isinstance(item, dict):
                        continue
                    row = dict(item)
                    for fk_col_name, parent_col_name in fk_specs:
                        row[fk_col_name] = record.get(parent_col_name)
                    rows.append(row)
            child_dfs[child["name"]] = (
                pd.json_normalize(rows)
                if rows
                else (pd.DataFrame(columns=[c.name for c in child["columns"]]))
            )

        out: Dict[str, pd.DataFrame] = {
            self.get_extraction_key(self._root["name"]): parent_df,
        }
        for name, df in child_dfs.items():
            out[self.get_extraction_key(name)] = df
        return out


class DataFrameExtractor(Extractor):
    """Extractor that wraps a pre-built ``pandas.DataFrame``.

    Useful for tests and notebook workflows where the input data is
    already in memory and no file IO is needed.

    Attributes:
        name: Logical table/file name under which the DataFrame is exposed.
        df: The DataFrame to expose.
        schema: ``Schema`` (SINGLE) whose ``datatypes()`` are applied via
            ``DataTypeConverter``. ``MULTI`` schemas are not supported.
    """

    def __init__(
        self,
        name: str,
        df: pd.DataFrame,
        schema: Schema,
        logger: Logger = None,
    ) -> None:
        # Construct a minimal pseudo-File so the base class plumbing
        # (extraction messages, etc.) keeps working without on-disk IO.
        class _MemoryFile:
            __slots__ = ("name",)

            def __init__(self, n: str) -> None:
                self.name = n

        super().__init__(_MemoryFile(name), logger)
        if not schema.is_single():
            raise ValueError(
                "DataFrameExtractor only supports SINGLE schemas; "
                f"got {schema.schema_type()}."
            )
        self._df = df
        self.schema = schema

    def extract(self) -> Dict[str, pd.DataFrame]:
        self._extraction_message()
        df = DataTypeConverter.convert_dtypes(
            self._df.copy(),
            self.schema.datatypes(),
            issues=self.conversion_issues,
            table_name=self.file.name,
        )
        self._extraction_success_message()
        return {self.file.name: df}


class ExtractionSequence:
    def __init__(
        self, extractors: List[Extractor] = None, logger: Logger = None
    ) -> None:
        self._extractors = extractors or []
        self._completed: bool = False
        self.logger = logger
        self._data = None
        self._conversion_issues: List[ConversionIssue] = []

    def run_extraction(self) -> Dict[str, pd.DataFrame]:
        data: Dict[str, pd.DataFrame] = {}
        all_issues: List[ConversionIssue] = []

        for extractor in self._extractors:
            extractor.conversion_issues = []  # reset before each run
            dfs: Dict[str, pd.DataFrame] = extractor.extract()
            data.update(dfs)
            all_issues.extend(extractor.conversion_issues)

        self._completed = True
        self._data = data
        self._conversion_issues = all_issues
        return data

    @property
    def completed(self) -> bool:
        return self._completed

    @property
    def data(self) -> Dict[str, pd.DataFrame]:
        if not self.completed:
            self.run_extraction()
        return self._data

    @property
    def conversion_issues(self) -> List[ConversionIssue]:
        """Return dtype-conversion failures collected during extraction.

        The ETL pipeline drains these and surfaces them as validation
        messages instead of letting them silently corrupt the data.
        """
        return list(self._conversion_issues)

    def add_extractor(self, extractor: Extractor) -> None:
        self._extractors.append(extractor)

    def add_extractors(self, extractors: List[Extractor]) -> None:
        for extractor in extractors:
            self.add_extractor(extractor)
