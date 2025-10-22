from abc import ABC, abstractmethod
from io import StringIO
from typing import Dict, List

import pandas as pd
import json

from algomancy.dataengine.schema import Schema, DataType
from algomancy.dataengine.file import File, XLSXFile, JSONFile, CSVFile
from algomancy.dashboardlogger.logger import Logger


class DateFormatError(Exception):
    pass


class DataTypeConverter:
    @staticmethod
    def convert_dtypes(df: pd.DataFrame, schema: Schema) -> pd.DataFrame:
        """
        Converts DataFrame columns to the specified data types in the schema.
        Attempts different localization options for numeric columns and date formats if the initial conversion fails.

        Args:
            df: The pandas DataFrame to convert
            schema: The Schema object containing the target data types for each column in the DataFrame

        Returns:
            DataFrame with converted data types where possible
        """

        result_df = df.copy()

        for column, target_type in schema.datatypes.items():
            if column not in result_df.columns:
                continue

            if target_type in (DataType.FLOAT, DataType.INTEGER):
                result_df = DataTypeConverter._convert_numeric_column(result_df, column, target_type)
            elif target_type == DataType.DATETIME:
                result_df = DataTypeConverter._convert_datetime_column(result_df, column)
            elif target_type == DataType.BOOLEAN:
                result_df = DataTypeConverter._convert_boolean_column(result_df, column)
            elif target_type == DataType.STRING:
                result_df = DataTypeConverter._convert_string_column(result_df, column)
            else:
                raise NotImplementedError(f"Unsupported data type: {target_type}")

        return result_df

    @staticmethod
    def _convert_numeric_column(df: pd.DataFrame, column: str, target_type: DataType) -> pd.DataFrame:
        """Convert a column to a numeric type, handling different number formats."""
        try:
            # Standard conversion first
            df[column] = df[column].astype(target_type)
        except (ValueError, TypeError):
            # Try fixing common localization issues
            try:
                # Try European format (comma as decimal separator)
                if df[column].dtype == 'object' and len(df[column]) > 0:
                    if target_type == DataType.FLOAT:
                        temp_values = df[column].str.replace(',', '.').astype(DataType.FLOAT)
                        df[column] = temp_values
                    else:
                        # For integers, first convert to float (handling comma separators) then to int
                        temp_values = df[column].str.replace(',', '.').astype(DataType.FLOAT).astype(DataType.INTEGER)
                        df[column] = temp_values
            except (ValueError, TypeError, AttributeError, IndexError):
                try:
                    # Try with thousands separator removal
                    if df[column].dtype == 'object' and len(df[column]) > 0:
                        if target_type == DataType.FLOAT:
                            temp_values = df[column].str.replace(',', '').astype(DataType.FLOAT)
                            df[column] = temp_values
                        else:
                            temp_values = df[column].str.replace(',', '').astype(DataType.INTEGER)
                            df[column] = temp_values
                except (ValueError, TypeError, AttributeError, IndexError) as e:
                    print(e)
                    # skip and wait for validation
                    pass
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
            for date_format in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y']:
                try:
                    temp = pd.to_datetime(df[column], format=date_format)
                    df[column] = temp
                    success = True
                    break  # Break the loop if conversion succeeds
                except (ValueError, TypeError, AttributeError):
                    continue  # Try next format
            if not success:
                raise DateFormatError(f"Could not convert column '{column}' to date format.")
        return df

    @staticmethod
    def _convert_datetime_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
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
        except (ValueError, TypeError):
            # Try different datetime formats
            for datetime_format in ['%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S',
                                    '%d/%m/%Y %H:%M:%S', '%Y-%m-%dT%H:%M:%S',
                                    '%d.%m.%Y %H:%M:%S']:
                try:
                    temp = pd.to_datetime(df[column], format=datetime_format)
                    df[column] = temp
                    break  # Break the loop if conversion succeeds
                except (ValueError, TypeError, AttributeError):
                    continue  # Try next format
        return df

    @staticmethod
    def _convert_boolean_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Convert a column to boolean type, handling various representations."""
        import pandas as pd
        import numpy as np

        try:
            df[column] = df[column].astype(DataType.BOOLEAN)
        except (ValueError, TypeError):
            try:
                # Try common boolean string representations
                bool_map = {
                    'true': True, 'yes': True, 'y': True, '1': True, 't': True,
                    'false': False, 'no': False, 'n': False, '0': False, 'f': False
                }

                if df[column].dtype == 'object':  # Only apply for string types
                    temp = df[column].astype(str).str.lower().map(bool_map)
                    # Only update if mapping was successful (not NaN)
                    mask = ~temp.isna()
                    if mask.any():
                        df.loc[mask, column] = temp[mask]
                        # Try to convert the whole column to bool if all values were mapped
                        if mask.all():
                            df[column] = df[column].astype(DataType.BOOLEAN)
            except (ValueError, TypeError, AttributeError) as e:
                print(e)
                # Skip if conversion fails
                pass
        return df

    @staticmethod
    def _convert_string_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Convert a column to other non-specialized types."""
        try:
            # Update the column in the original dataframe with the target type
            df[column] = df[column].astype(DataType.STRING)
        except (ValueError, TypeError) as e:
            print(e)
            # skip and wait for validation
            pass
        return df


class Extractor(ABC):
    def __init__(
            self,
            file: File,
            logger: Logger = None
    ) -> None:
        self.file = file
        self.logger = logger

    def _extraction_message(self):
        if self.logger:
            self.logger.log(f'Extracting from {self.file.name}')

    def _extraction_success_message(self):
        if self.logger:
            self.logger.success(f'Extraction of {self.file.name} successful')

    @abstractmethod
    def extract(self) -> Dict[str, pd.DataFrame]:
        pass

class SingleExtractor(Extractor):
    def __init__(
            self,
            file: File,
            schema: Schema,
            logger: Logger = None
    ) -> None:
        super().__init__(file, logger)
        self.schema = schema

    def extract(self) -> Dict[str, pd.DataFrame]:
        """Returns Dict[name, dataframe], so each dataset is identifiable"""

        self._extraction_message()
        df = self._extract_file()
        df = DataTypeConverter.convert_dtypes(df, self.schema)
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
    def __init__(
            self,
            files: File,
            schemas: Dict[str, Schema],
            logger: Logger = None
    ) -> None:
        super().__init__(files, logger)
        self.schemas = schemas

    def _check_schemas(self, dfs: Dict[str, pd.DataFrame]):
        missing_keys = set(dfs.keys()) - set(self.schemas.keys())
        assert len(missing_keys) == 0, f"Missing schemas for keys: {missing_keys}"

    def extract(self) -> Dict[str, pd.DataFrame]:
        """Returns Dict[name, dataframe], so each dataset is identifiable"""

        self.extraction_message()

        dfs = self._extract_files()

        # Attemting to convert all dataframes with the corresponing schema
        # Before this we check if the keys of the schemas and the names of the extracted dataframes match
        self._check_schemas(dfs)
        dfs = {name: DataTypeConverter.convert_dtypes(df, self.schemas[name]) for name, df in dfs.items()}

        self.extraction_success_message()
        return dfs

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
        file_path: str
            The full path to the CSV file that needs to be processed.
        logger: Logger, optional
            An optional logger instance to log messages and errors.
        separator: str
            The delimiter string to use for parsing the CSV file
            (default is ";").
    """

    def __init__(
            self,
            file: CSVFile,
            schema: Schema,
            logger: Logger = None,
            separator: str = ";"
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

    JSONExtractor expects the JSON file to be formatted such that the root level is
    a list. Each item in the list represents a single record, and each record has
    some properties. The properties are represented as key-value pairs. If the value
    is a dictionary, it is treated as a nested object. Each nested object is converted
    to a column in the dataframe. If the value is a list, it is converted to a string.

    Attributes:
        file_path: str
            Path to the JSON file to be read.
        logger: Logger, optional
            Logger instance for logging messages. Defaults to None.
    """

    def __init__(
            self,
            file: JSONFile,
            schema: Schema,
            logger: Logger = None
    ) -> None:
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
        file: File
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
                sheet_name = content_obj["metadata"]["index_to_sheet_name"][str(sheet_name)]
            else:
                # Use the index directly to get from the list of sheet names
                try:
                    sheet_name = content_obj["metadata"]["sheet_names"][sheet_name]
                except IndexError:
                    raise ValueError(
                        f"Sheet index {sheet_name} is out of range. "
                        f"Available sheets: {content_obj['metadata']['sheet_names']}")

        # Check if the requested sheet exists
        if sheet_name not in content_obj["sheets"]:
            raise ValueError(
                f"Sheet '{sheet_name}' not found in Excel file. "
                f"Available sheets: {content_obj['metadata']['sheet_names']}")

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
        file: File
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
            schemas: Dict[str, Schema],
            sheet_names: List[str],
            logger: Logger = None,
    ) -> None:
        super().__init__(file, schemas, logger)
        self._sheet_names = sheet_names
        self._single_sheet_extractors = [XLSXSingleExtractor(file, schemas[sheet_name], sheet_name) for sheet_name in sheet_names]

    def _extract_files(self) -> Dict[str, pd.DataFrame]:
        dfs = {}
        for extractor in self._single_sheet_extractors:
            dfs.update(extractor.extract())
        return dfs
