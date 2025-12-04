from abc import ABC
from io import BytesIO
from typing import Dict
import pandas as pd
import json
import base64

from algomancy.dataengine.inputfileconfiguration import FileExtension


class File(ABC):
    def __init__(
        self,
        name: str,
        extension: FileExtension,
        path: str = None,
        content: str = None,
    ):
        self.name: str = name
        self.path: str | None = path
        self.extension: FileExtension = extension
        self.content = None

        if content is not None:
            self.content: str = content
        elif path is not None:
            self.content = self.read_contents_from_path()

    def read_contents_from_path(self) -> str:
        try:
            with open(self.path, "r") as f:
                return f.read()
        except Exception as e:
            print(e)
            raise e

    @staticmethod
    def _set_content_from_uploader(content: str) -> str:
        try:
            # Extract the base64 content from the data URI
            content_type, content_string = content.split(",", 1)
            decoded = base64.b64decode(content_string)

            if "csv" in content_type.lower():
                # transform to textformat
                csv_file = decoded.decode("utf-8")

                return csv_file

            elif "json" in content_type.lower():
                # Transform the decoded data to json
                json_data = json.loads(decoded)

                return json.dumps(json_data)
            else:
                raise ValueError("Invalid content type.")

        except Exception as e:
            print(f"Error reading JSON file from uploader: {e}")
            raise e


class CSVFile(File):
    def __init__(
        self,
        name: str,
        path: str = None,
        content: str = None,
    ):
        super().__init__(name, FileExtension.CSV, path, None)
        if content is not None:
            self.content = self._set_content_from_uploader(content)


class JSONFile(File):
    def __init__(
        self,
        name: str,
        path: str = None,
        content: str = None,
    ):
        super().__init__(name, FileExtension.JSON, path, None)
        if content is not None:
            self.content = self._set_content_from_uploader(content)


class XLSXFile(File):
    def __init__(self, name: str, path: str = None, content: str = None):
        super().__init__(name, FileExtension.XLSX, path, None)
        self.index_to_sheet_name: Dict[int, str] = {}
        if content is not None:
            self.content: str = self._set_content_from_uploader(content)

    def _set_content_from_uploader(self, content: str) -> str:
        """
        XLSX content is treated individually. The content is extracted from the data URI,
        and stored in a dictionary. Each sheet is converted to JSON and stored, to allow
        the XLSX extractor to access the appropriate sheet.
        """
        try:
            # Extract the base64 content from the data URI
            content_type, content_string = content.split(",", 1)
            decoded = base64.b64decode(content_string)

            # Use BytesIO instead of StringIO for binary data
            excel_file = pd.ExcelFile(BytesIO(decoded))

            # Return as JSON string
            return self._process_excel_file(excel_file)

        except Exception as e:
            print(f"Error reading Excel file from uploader: {e}")
            raise e

    def read_contents_from_path(self) -> str:
        try:
            # Read all sheets from the Excel file
            excel_file = pd.ExcelFile(self.path)
            return self._process_excel_file(excel_file)

        except Exception as e:
            print(f"Error reading Excel file {self.path}: {e}")
            raise e

    def _process_excel_file(self, excel_file):
        sheet_names = excel_file.sheet_names

        # Store mapping of index to sheet name
        self.index_to_sheet_name = {i: name for i, name in enumerate(sheet_names)}

        # Read each sheet and convert to JSON
        all_sheets_data = {}
        for i, sheet_name in enumerate(sheet_names):
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            json_data = df.to_json(orient="records")
            # self.sheet_data[sheet_name] = json_data
            all_sheets_data[sheet_name] = json.loads(json_data)

        # Create a combined structure with metadata and all sheets
        result = {
            "metadata": {
                "sheet_count": len(sheet_names),
                "sheet_names": sheet_names,
                "index_to_sheet_name": self.index_to_sheet_name,
            },
            "sheets": all_sheets_data,
        }

        # Return as JSON string
        return json.dumps(result)
