import argparse
import importlib
import os
import sys
from typing import Callable


def _ensure_dev_path():
    here = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.abspath(os.path.join(here, "..", "..", "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    try:
        from algomancy_cli.cli_configuration import CliConfiguration  # noqa: F401
        from algomancy_cli.cli_launcher import CliLauncher  # noqa: F401

        return
    except Exception:
        pass


_ensure_dev_path()

from algomancy_cli.cli_configuration import CliConfiguration  # type: ignore  # noqa: E402
from algomancy_cli.cli_launcher import CliLauncher  # type: ignore  # noqa: E402


def _parse_args():
    parser = argparse.ArgumentParser(description="Algomancy CLI shell")
    parser.add_argument(
        "--config-callback",
        type=str,
        default=None,
        help=(
            "Callback to construct CliConfiguration, in the form 'module:function'. "
            "The function must return a CliConfiguration instance."
        ),
    )
    parser.add_argument(
        "--example",
        action="store_true",
        help="Use the example configuration bundled in this repository (for development).",
    )
    return parser.parse_args()


def _load_config_from_callback(spec: str) -> CliConfiguration:
    if ":" not in spec:
        raise ValueError("--config-callback must be in 'module:function' form")
    module_name, func_name = spec.split(":", 1)
    module = importlib.import_module(module_name)
    func: Callable[[], CliConfiguration] = getattr(module, func_name)
    cfg = func()
    if not isinstance(cfg, CliConfiguration):
        raise TypeError("Config callback did not return CliConfiguration")
    return cfg


def _build_example_config() -> CliConfiguration:
    # These imports rely on this repo's example package being available in the workspace
    from example.data_handling.schemas import example_schemas
    from example.data_handling.factories import ExampleETLFactory
    from example.templates import kpi_templates, algorithm_templates

    from algomancy_data import DataSource

    return CliConfiguration(
        data_path="example/data",
        has_persistent_state=True,
        etl_factory=ExampleETLFactory,
        kpi_templates=kpi_templates,
        algo_templates=algorithm_templates,
        input_configs=example_schemas,
        data_object_type=DataSource,
        autocreate=True,
        default_algo="Slow",
        default_algo_params_values={"duration": 1},
        autorun=True,
        title="Algomancy CLI (Example)",
    )


def main():
    args = _parse_args()
    if args.config_callback:
        cfg = _load_config_from_callback(args.config_callback)
    elif args.example:
        cfg = _build_example_config()
    else:
        print("Either pass --config-callback module:function or use --example")
        sys.exit(2)

    shell = CliLauncher.build(cfg)
    CliLauncher.run(shell)


if __name__ == "__main__":
    main()
