"""Console entry point for the ``algomancy-api`` script.

Load a user's :class:`ApiConfiguration` via a ``module:function`` callback
(or use the bundled example config), then hand the resulting app to
:class:`ApiLauncher` to serve with uvicorn.

Usage
-----

::

    algomancy-api --config-callback myapp.api:make_config
    algomancy-api --example
    algomancy-api --example --host 0.0.0.0 --port 9000
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from typing import Callable


def _ensure_dev_path() -> None:
    """When running from a source checkout, put the repo root on ``sys.path``
    so a callback can refer to top-level modules like ``example.api``."""
    here = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.abspath(os.path.join(here, "..", "..", "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


_ensure_dev_path()

# Imports below depend on _ensure_dev_path running first when invoked from a
# source checkout.
from algomancy_api.api_configuration import ApiConfiguration  # noqa: E402
from algomancy_api.api_launcher import ApiLauncher  # noqa: E402


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Algomancy HTTP API (FastAPI + uvicorn)."
    )
    parser.add_argument(
        "--config-callback",
        type=str,
        default=None,
        help=(
            "Callback that returns an ApiConfiguration, in the form "
            "'module:function'. The function must take no arguments."
        ),
    )
    parser.add_argument(
        "--example",
        action="store_true",
        help="Use the example configuration bundled in this repository.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Bind address (overrides the value from the config).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Bind port (overrides the value from the config).",
    )
    return parser.parse_args(argv)


def _load_config_from_callback(spec: str) -> ApiConfiguration:
    if ":" not in spec:
        raise ValueError("--config-callback must be in 'module:function' form")
    module_name, func_name = spec.split(":", 1)
    module = importlib.import_module(module_name)
    func: Callable[[], ApiConfiguration] = getattr(module, func_name)
    cfg = func()
    if not isinstance(cfg, ApiConfiguration):
        raise TypeError(
            f"Config callback must return an ApiConfiguration; got {type(cfg).__name__}"
        )
    return cfg


def build_example_config() -> ApiConfiguration:
    """Construct an ApiConfiguration backed by the bundled example wiring.

    Exposed at module scope (rather than as a private ``_build_example_config``)
    so tests and downstream code can reuse it.
    """
    # These imports rely on the repo root being on ``sys.path`` (handled in
    # ``_ensure_dev_path`` when running from a source checkout).
    from example.data_handling.schemas import example_schemas
    from example.data_handling.factories import ExampleETLFactory
    from example.templates import kpi_templates, algorithm_templates
    from algomancy_data import DataSource

    return ApiConfiguration(
        data_path="example/data",
        has_persistent_state=True,
        etl_factory=ExampleETLFactory,
        kpi_templates=kpi_templates,
        algo_templates=algorithm_templates,
        schemas=example_schemas,
        data_object_type=DataSource,
        autocreate=True,
        default_algo="Instant",
        default_algo_params_values={},
        autorun=False,
        title="Algomancy API (Example)",
    )


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    if args.config_callback:
        cfg = _load_config_from_callback(args.config_callback)
    elif args.example:
        cfg = build_example_config()
    else:
        print("Either pass --config-callback module:function or use --example")
        sys.exit(2)

    app = ApiLauncher.build(cfg)
    ApiLauncher.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
