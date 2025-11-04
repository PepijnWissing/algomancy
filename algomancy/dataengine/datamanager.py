import os
import shutil
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Type, TypeVar

import pandas as pd

from algomancy.dataengine.datasource import DataSource, DataSourceType
from algomancy.dataengine.etl import ETLFactory, ETLConstructionError
from algomancy.dataengine.inputfileconfiguration import InputFileConfiguration, FileExtension
from algomancy.dataengine.validator import Validator, ValidationError, ValidationSequence
from algomancy.dataengine.file import File, CSVFile, JSONFile, XLSXFile
from algomancy.dashboardlogger.logger import Logger

E = TypeVar("E", bound=ETLFactory)
DOT = TypeVar("DOT", bound=DataSource)


class DataManager(ABC):
    """
    Handles all data-related operations: loading, deriving, deleting, and storing datasets.
    """

    def __init__(
            self,
            etl_factory: type[E],
            input_configs: List[InputFileConfiguration],
            save_type: str,
            data_object_type: type[DOT],
            logger: Logger | None = None
    ) -> None:
        self.logger = logger
        self._etl_factory = etl_factory(input_configs, self.logger)
        self._input_configs = input_configs
        self._data: Dict[str, DataSource] = {}
        self._save_type = save_type
        self._data_object_type: type[DOT] = data_object_type

    @property
    def data_object_type(self):
        return self._data_object_type

    @abstractmethod
    def startup(self):
        raise NotImplementedError

    # Utility
    def log(self, message: str):
        if self.logger:
            self.logger.log(message)

    # Accessors
    def get_data_keys(self) -> List[str]:
        return list(self._data.keys())

    def get_data(self, data_key: str) -> DataSource | None:
        return self._data.get(data_key)

    # Derive/Delete
    def derive_data(self, derive_from_key: str, new_data_key: str) -> None:
        assert derive_from_key in self.get_data_keys(), f"Data '{derive_from_key}' not found."
        assert new_data_key not in self.get_data_keys(), f"Data '{new_data_key}' already exists."

        new_data = self._data_object_type(ds_type=DataSourceType.DERIVED_DATA, name=new_data_key)
        new_data.copy_contents_from(ds_to_copy=self.get_data(derive_from_key))

        self._data[new_data_key] = new_data
        self.log(f"Derived data '{new_data_key}' derived from '{derive_from_key}'.")

    def add_data_source(self, data_source: DataSource) -> None:
        # Add to the data dictionary
        self._data[data_source.name] = data_source
        self.log(f"Loaded DataSource '{data_source.name}' from {self._save_type} file.")

    @abstractmethod
    def delete_data(self, data_key: str, prevent_masterdata_removal: bool = False) -> None:
        raise NotImplementedError

    @staticmethod
    def check_existence_of_files(
            file_name_to_path: List[Tuple[str, str]]
    ) -> None:
        for file, path in file_name_to_path:
            if not os.path.exists(path):
                raise ETLConstructionError(f"File at path '{path}' does not exist.")

    @staticmethod
    def prepare_files(
            file_items_with_content: List[Tuple[str, str, str]] = None,
            file_items_with_path: List[Tuple[str, str]] = None,
    ) -> Dict[str, File]:
        if file_items_with_content:
            return DataManager._prepare_files_from_content(file_items_with_content)
        elif file_items_with_path:
            return DataManager._prepare_files_from_path(file_items_with_path)
        else:
            raise ETLConstructionError("No file data provided.")

    @staticmethod
    def _add_to_files(files, name, extension, content = None, path = None) -> None:
        assert path or content, "Either path or content must be provided."

        if extension == FileExtension.CSV.lower():
            files[name] = CSVFile(name=name, content=content, path=path)
        elif extension == FileExtension.JSON.lower():
            files[name] = JSONFile(name=name, content=content, path=path)
        elif extension == FileExtension.XLSX.lower():
            files[name] = XLSXFile(name=name, content=content, path=path)
        else:
            raise ETLConstructionError(f"Unsupported file type: '{extension}'.")

    @staticmethod
    def _prepare_files_from_content(
            file_items: List[Tuple[str, str, str]] = None,
    ) -> Dict[str, File]:
        files = {}
        for name, extension, content in file_items:
            DataManager._add_to_files(files, name, extension, content=content)

        return files

    @staticmethod
    def _prepare_files_from_path(
            file_items: List[Tuple[str, str]]
    ) -> Dict[str, File]:
        DataManager.check_existence_of_files(file_items)
        files = {}
        for file, path in file_items:
            extension = path.split(".")[-1].lower()
            DataManager._add_to_files(files, file, extension, path=path)

        return files

    def etl_data(self, files: Dict[str, File], dataset_name: str) -> None:
        """
        todo write header

        raises:
            ETLConstructionError: if ETL pipeline construction fails.
            ValidationError: if data validation yields critical errors.
        """
        etl = self._etl_factory.build_pipeline(dataset_name, files, self.logger)  # Raises ETLError
        self.log(f"ETL pipeline for dataset '{dataset_name}' created.")
        ds = etl.run()  # Raises ValidationError
        self._data[dataset_name] = ds
        if self.logger:
            self.logger.success(f"ETL pipeline for dataset '{dataset_name}' completed.")

    def create_validation_sequence(self) -> ValidationSequence:
        return self._etl_factory.create_validation_sequence()


class StatelessDataManager(DataManager):
    def __init__(
            self,
            etl_factory: type[ETLFactory],
            input_configs: List[InputFileConfiguration],
            save_type: str,
            data_object_type: type[DOT],
            logger: Logger | None = None
    ):
        super().__init__(etl_factory, input_configs, save_type, data_object_type, logger)
        self._data: Dict[str, DataSource] = {}

    def startup(self):
        # Stateless data manager does not need to perform any additional actions on startup
        pass

    def delete_data(self, data_key: str, prevent_masterdata_removal: bool = False) -> None:
        assert data_key in self.get_data_keys(), f"Data '{data_key}' not found."
        # note: responsibility for checking scenario usage resides in callers

        del self._data[data_key]
        self.log(f"Data '{data_key}' deleted.")


class StatefulDataManager(DataManager):
    def __init__(
            self,
            etl_factory: type[ETLFactory],
            input_configs: List[InputFileConfiguration],
            data_folder: str,
            save_type: str,
            data_object_type: type[DOT],
            logger: Logger | None = None
    ):
        super().__init__(etl_factory, input_configs, save_type, data_object_type, logger)
        self._data_folder = data_folder
        self._data: Dict[str, DOT] = {}  # Loading

    def startup(self):
        try:
            self._load_data_from_data_folder()
            self.log(f"Data folder '{self._data_folder}' loaded.")
        except Exception as e:
            if self.logger:
                self.logger.error(f'Data load on startup failed: {str(e)}')
                self.logger.log_traceback(e)
            print(e)

    def load_data_from_file(self, file_path: str) -> None:
        # Create a DataSource from the parquet bytes
        if self._save_type == "parquet":

            # Read the file content as bytes
            with open(file_path, "rb") as f:
                parquet_bytes = f.read()
            data_source = self.data_object_type.from_parquet_bytes(parquet_bytes)

        elif self._save_type == "json":
            # Read the file content as text
            with open(file_path, "r", encoding="utf-8") as f:
                json_string = f.read()
            data_source = self.data_object_type.from_json(json_string)
        else:
            raise Exception(f"Unsupported save type: {self._save_type}")

        self.add_data_source(data_source)

    def _load_data_from_data_folder(self) -> None:
        """
        Loads all parquet files from the data folder and creates DataSource objects.
        Each parquet file is expected to be a serialized DataSource.
        """
        import os

        # Check if the folder exists
        if not os.path.exists(self._data_folder):
            self.logger.warning(f"Data folder '{self._data_folder}' does not exist.")
            return

        # List all files in the data folder
        items = os.listdir(self._data_folder)

        for item in items:

            item_path = os.path.join(self._data_folder, item)

            # If it's a file, try to load it as a file of the appropriate type
            if os.path.isfile(item_path):
                # Verify that item is of the appropriate data format
                if not item.endswith(f".{self._save_type}"):
                    self.logger.warning(f"Skipping file '{item_path}' because it is not a {self._save_type} file.")
                    continue

                try:
                    self.load_data_from_file(item_path)

                except Exception as e:
                    self.logger.error(f"Failed to load file '{item_path}' as a DataSource: {str(e)}")
                    self.traceback = self.logger.log_traceback(e)

            # If it's a directory, run ETL
            elif os.path.isdir(item_path):
                try:
                    self.load_data_from_dir(item)
                except Exception as e:
                    self.logger.error(f"Failed to load directory '{item_path}' as a DataSource: {str(e)}")
                    self.logger.log_traceback(e)

    def load_data_from_dir(self, directory: str, root: str | None = None) -> None:
        if root is None:
            root = self._data_folder

        # Retrieve files from directory
        dataset_name = directory
        dataset_path = os.path.join(root, directory)
        files = os.listdir(dataset_path)

        # Compile the file-items
        file_items_with_path = [(file.split(".")[0], os.path.join(dataset_path, file)) for file in files]

        # Run ETL
        prepared_files = self.prepare_files(file_items_with_path=file_items_with_path)
        self.etl_data(prepared_files, dataset_name)

    def delete_data(self, data_key: str, prevent_masterdata_removal: bool = False) -> None:
        assert data_key in self.get_data_keys(), f"Data '{data_key}' not found."
        # note: responsibility for checking scenario usage resides in callers

        # Delete files if applicable
        if self._data[data_key].is_master_data():
            directory = os.path.join(self._data_folder, data_key)
            if os.path.isdir(directory):
                shutil.rmtree(directory)
            elif os.path.isfile(directory):
                os.remove(directory)

        del self._data[data_key]
        self.log(f"Data '{data_key}' deleted.")

    # Store new dataset to data folder (as CSVs) and keep in memory
    def store_data(self, dataset_name: str, data: Dict[str, pd.DataFrame], USE_OLD_VERSION=True) -> None:
        if not USE_OLD_VERSION:
            raise NotImplementedError
        else:
            import os as _os
            target_dir = _os.path.join(self._data_folder, dataset_name)
            if _os.path.exists(target_dir):
                raise Exception(f"Directory '{dataset_name}' already exists in '{self._data_folder}'")
            _os.makedirs(target_dir)

            # Write each DataFrame to a CSV named after its key
            for key, df in data.items():
                file_path = _os.path.join(target_dir, f"{key}.csv")
                df.to_csv(file_path, index=False, sep=";")

            # Also keep in memory
            ds = self.data_object_type(name=dataset_name, ds_type=DataSourceType.DERIVED_DATA)
            for key, df in data.items():
                ds.add_table(key, df)
            self._data[dataset_name] = ds
            self.log(f"Stored dataset '{dataset_name}' to disk and memory.")

    def store_data_source_as_parquet(self, dataset_name: str, allow_overwrite: bool = False):
        import os as _os
        file_name = _os.path.join(self._data_folder, f'{dataset_name}.parquet', )
        if _os.path.exists(file_name) and not allow_overwrite:
            raise Exception(f"Directory '{dataset_name}' already exists in '{self._data_folder}'")

        # Retrieve datasource
        data_source = self.get_data(dataset_name)

        # check existence
        assert data_source is not None, f"Data source '{dataset_name}' not found."

        # Serialize it to parquet bytes
        parquet_bytes = data_source.to_parquet_bytes()

        # store bytes in file
        with open(file_name, "wb") as f:
            f.write(parquet_bytes)

    def store_data_source_as_json(self, dataset_name: str, allow_overwrite: bool = False):
        import os as _os
        file_name = _os.path.join(self._data_folder, f'{dataset_name}.json')
        if _os.path.exists(file_name) and not allow_overwrite:
            raise Exception(f"Directory '{dataset_name}' already exists in '{self._data_folder}'")

        # Retrieve datasource
        data_source = self.get_data(dataset_name)

        # check existence
        assert data_source is not None, f"Data source '{dataset_name}' not found."

        # Serialize it to parquet bytes
        json_content = data_source.to_json()

        # store bytes in file
        with open(file_name, "wb") as f:
            f.write(json_content.encode('utf-8'))
