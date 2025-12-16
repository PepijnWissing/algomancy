from __future__ import annotations

from typing import Any, Dict

from algomancy_scenario.core_configuration import CoreConfiguration


class CliConfiguration(CoreConfiguration):
    """Configuration for the CLI application.

    Extends the core configuration with CLI-specific options.
    """

    def __init__(
        self,
        # core parameters (see CoreConfiguration)
        data_path: str = "data",
        has_persistent_state: bool = False,
        save_type: str | None = "json",
        data_object_type: type | None = None,
        etl_factory: Any | None = None,
        kpi_templates: Dict[str, Any] | None = None,
        algo_templates: Dict[str, Any] | None = None,
        input_configs: list | None = None,
        autocreate: bool | None = None,
        default_algo: str | None = None,
        default_algo_params_values: Dict[str, Any] | None = None,
        autorun: bool | None = None,
        title: str = "Algomancy CLI",
        # CLI specific
        verbose: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data_path=data_path,
            has_persistent_state=has_persistent_state,
            save_type=save_type,
            data_object_type=data_object_type,
            etl_factory=etl_factory,
            kpi_templates=kpi_templates,
            algo_templates=algo_templates,
            input_configs=input_configs,
            autocreate=autocreate,
            default_algo=default_algo,
            default_algo_params_values=default_algo_params_values,
            autorun=autorun,
            title=title,
            **kwargs,
        )

        self.verbose = verbose
        self._validate_cli()

    def as_dict(self) -> Dict[str, Any]:
        base = super().as_dict()
        base.update(
            {
                "verbose": self.verbose,
            }
        )
        return base

    def _validate_cli(self) -> None:
        if self.verbose is None:
            raise ValueError(
                "Boolean configuration 'verbose' must be set to True or False, not None"
            )
