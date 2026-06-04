"""Concrete ``DataSource`` for the warehouse example.

Demonstrates how a user-defined data source declares per-scenario knobs by
overriding ``initialize_data_parameters``. The framework persists user-supplied
values on each scenario and pushes them onto the algorithm via
``BaseAlgorithm.set_data_params`` before ``run()``; the algorithm decides
whether and how to act on them.

For this example, the dataset exposes two knobs:

* ``category_filter`` — only consider items in selected categories
* ``min_daily_picks`` — drop low-traffic items below this threshold

``GreedySlotting`` reads these from ``self.data_params`` and pre-filters its
input accordingly. Algorithms that don't care simply ignore the params.
"""

from __future__ import annotations

from algomancy_data import DataSource
from algomancy_utils.baseparameterset import (
    BaseParameterSet,
    IntegerParameter,
    MultiEnumParameter,
)


class WarehouseDataParameters(BaseParameterSet):
    """Per-scenario knobs for the warehouse dataset."""

    def __init__(self, categories: list[str]) -> None:
        super().__init__(name="Warehouse Data")
        # MultiEnumParameter requires at least one choice; fall back to a
        # sentinel so the set is always well-formed even before ETL has run.
        choices = categories if categories else ["(none)"]
        self.add_parameters(
            [
                MultiEnumParameter(
                    name="category_filter",
                    choices=choices,
                    value=list(choices),
                ),
                IntegerParameter(
                    name="min_daily_picks",
                    minvalue=0,
                    default=0,
                ),
            ]
        )

    def validate(self) -> None:
        pass


class WarehouseDataSource(DataSource):
    """Warehouse-flavoured DataSource that declares per-scenario filtering knobs."""

    def initialize_data_parameters(self) -> BaseParameterSet:
        categories: list[str] = []
        sku_table = self.tables.get("sku_data") if self.tables else None
        if sku_table is not None and "category" in sku_table.columns:
            categories = sorted(
                str(c) for c in sku_table["category"].dropna().unique().tolist()
            )
        return WarehouseDataParameters(categories=categories)
