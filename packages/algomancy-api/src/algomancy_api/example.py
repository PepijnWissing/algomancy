"""Bundled example wiring for the Algomancy HTTP API.

Use this as a one-liner when you want a working server backed by the
``example/`` package in the repo::

    from algomancy_api import ApiLauncher
    from algomancy_api.example import build_example_config

    ApiLauncher.run(ApiLauncher.build(build_example_config()))

The ``example.*`` imports below assume the repo root is on ``sys.path``
(true when running from a source checkout or invoking pytest from the
repo root).
"""

from __future__ import annotations

from .api_configuration import ApiConfiguration


def build_example_config() -> ApiConfiguration:
    """Construct an ApiConfiguration backed by the bundled example wiring."""
    from example.data_handling.schemas import example_schemas
    from example.data_handling.factories import ExampleETLFactory
    from example.templates import kpis, algorithms
    from algomancy_data import DataSource

    return ApiConfiguration(
        data_path="example/data",
        has_persistent_state=True,
        etl_factory=ExampleETLFactory,
        kpis=kpis,
        algorithms=algorithms,
        schemas=example_schemas,
        data_object_type=DataSource,
        autocreate=True,
        default_algo="Instant",
        default_algo_params_values={},
        autorun=False,
        title="Algomancy API (Example)",
    )
