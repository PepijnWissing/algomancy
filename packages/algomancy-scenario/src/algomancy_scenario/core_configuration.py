from __future__ import annotations

import os
from typing import Any, Dict, List, Type

from algomancy_data import InputFileConfiguration, BASE_DATA_BOUND
from algomancy_scenario import AlgorithmFactory, ALGORITHM, BASE_KPI


class CoreConfiguration:
    """
    Core configuration shared by GUI and CLI.

    Contains only fields that are not GUI- or CLI-specific.
    Validation is executed on construction.
    """

    def __init__(
        self,
        # === path specifications ===
        data_path: str = "data",
        # === data manager configuration ===
        has_persistent_state: bool = False,
        save_type: str | None = "json",
        data_object_type: type[BASE_DATA_BOUND] | None = None,
        # === scenario manager configuration ===
        etl_factory: Any | None = None,
        kpi_templates: Dict[str, Type[BASE_KPI]] | None = None,
        algo_templates: Dict[str, Type[ALGORITHM]] | None = None,
        input_configs: List[InputFileConfiguration] | None = None,
        # === auto start/create features ===
        autocreate: bool | None = None,
        default_algo: str | None = None,
        default_algo_params_values: Dict[str, Any] | None = None,
        autorun: bool | None = None,
        # === misc (core) ===
        title: str = "Algomancy",
        **_: Any,
    ) -> None:
        # paths
        self.data_path = data_path

        # data / scenario manager
        self.has_persistent_state = has_persistent_state
        self.save_type = save_type
        self.data_object_type = data_object_type
        self.etl_factory = etl_factory
        self.kpi_templates = kpi_templates
        self.algo_templates = algo_templates
        self.input_configs = input_configs
        self.autocreate = autocreate
        self.default_algo = default_algo
        self.default_algo_params_values = default_algo_params_values
        self.autorun = autorun

        # misc
        self.title = title

        self._validate_core()

    # ----- public API -----
    def as_dict(self) -> Dict[str, Any]:
        return {
            "data_path": self.data_path,
            "has_persistent_state": self.has_persistent_state,
            "save_type": self.save_type,
            "data_object_type": self.data_object_type,
            "etl_factory": self.etl_factory,
            "kpi_templates": self.kpi_templates,
            "algo_templates": self.algo_templates,
            "input_configs": self.input_configs,
            "autocreate": self.autocreate,
            "default_algo": self.default_algo,
            "default_algo_params_values": self.default_algo_params_values,
            "autorun": self.autorun,
            "title": self.title,
        }

    # ----- validation -----
    def _validate_core(self) -> None:
        self._validate_paths_core()
        self._validate_values_core()
        self._validate_algorithm_parameters_core()

    def _validate_paths_core(self) -> None:
        if self.has_persistent_state:
            if self.data_path is None or self.data_path == "":
                raise ValueError("data_path must be provided")
            if not os.path.isdir(self.data_path):
                raise ValueError(
                    f"data_path does not exist or is not a directory: {self.data_path}"
                )

    def _validate_values_core(self) -> None:
        # required non-null entries for scenario/data managers
        required_fields = {
            "etl_factory": self.etl_factory,
            "kpi_templates": self.kpi_templates,
            "algo_templates": self.algo_templates,
            "input_configs": self.input_configs,
            "data_object_type": self.data_object_type,
        }
        missing = [k for k, v in required_fields.items() if v is None]
        if missing:
            raise ValueError(
                f"Missing required configuration fields: {', '.join(missing)}"
            )

        # booleans allowed to be False, but must not be None if specified
        for name, val in {
            "has_persistent_state": self.has_persistent_state,
            "autocreate": self.autocreate,
            "autorun": self.autorun,
        }.items():
            if val is None:
                raise ValueError(
                    f"Boolean configuration '{name}' must be set to True or False, not None"
                )

        # save type
        if self.save_type is None:
            raise ValueError("save_type must be set to 'json' or 'parquet'")
        if self.save_type not in {"json", "parquet"}:
            raise ValueError("save_type must be either 'json' or 'parquet'")

        # title
        if not isinstance(self.title, str) or self.title.strip() == "":
            raise ValueError("title must be a non-empty string")

    def _validate_algorithm_parameters_core(self) -> None:
        if self.autocreate:
            tmp_factory = AlgorithmFactory(self.algo_templates)
            test_algorithm = tmp_factory.create(
                self.default_algo, self.default_algo_params_values
            )
            assert test_algorithm.healthcheck(), "Failed to create default algorithm"
