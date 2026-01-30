"""Transformation primitives for ETL pipelines.

Defines the abstract ``Transformer`` contract and a few simple concrete
transformers, as well as a ``TransformationSequence`` to compose multiple
transformers into a single pipeline step.
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import List
from algomancy_utils import Logger
from copy import deepcopy


class Transformer(ABC):
    """Base class for a transformation step operating on tabular data.

    Subclasses implement ``transform`` and can mutate the provided mapping of
    DataFrames in-place or return a new mapping where applicable.
    """

    def __init__(self, name: str = "Abstract Transformer", logger=None) -> None:
        self.name = name
        self._logger = logger

    @abstractmethod
    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        """Apply the transformation to the provided data.

        Args:
            data: Mapping from table name to pandas DataFrame. Implementations
                may mutate this mapping in place or create/replace entries.
        """
        pass


def fill_empty(data: pd.DataFrame) -> pd.DataFrame:
    """Forward-fill missing values across columns in a single row.

    Args:
        data: DataFrame to fill.

    Returns:
        DataFrame with values forward-filled along axis=1.
    """
    return data.fillna(method="ffill", axis=1)


def drop_empty(data: pd.DataFrame) -> pd.DataFrame:
    """Drop rows containing any NA values.

    Args:
        data: Input DataFrame.

    Returns:
        DataFrame without rows containing NA values.
    """
    return data.dropna()


class NoopTransformer(Transformer):
    """Transformer that returns the input data unchanged."""

    def __init__(self, logger=None) -> None:
        super().__init__(name="No Operation Transformer", logger=logger)

    def transform(self, data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        if self._logger:
            self._logger.log("No operation transformer called")
        return data


class CleanTransformer(Transformer):
    """Basic cleanup: drop NA rows and normalize column names to lowercase."""

    def __init__(self, logger=None) -> None:
        super().__init__(name="Standard Transformer", logger=logger)

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        if self._logger:
            self._logger.log("Cleaning dataframes (dropna, lowercase columns)")
        for name, df in data.items():
            df = df.dropna()
            df.columns = [c.lower().strip() for c in df.columns]


class JoinTransformer(Transformer):
    """Join two input tables and write the result to a new table key.

    Attributes:
        left: Name of the left table to join.
        right: Name of the right table to join.
        on: Column name to join on.
        output: Key under which the merged table is stored.
    """

    def __init__(
        self, left: str, right: str, on: str, output: str, logger=None
    ) -> None:
        super().__init__(name="Join transformer", logger=logger)
        self.left = left
        self.right = right
        self.on = on
        self.output = output

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        if self._logger:
            self._logger.log(
                f"Joining '{self.left}' and '{self.right}' on '{self.on}' into '{self.output}'"
            )
        merged = data[self.left].merge(data[self.right], on=self.on)
        data[self.output] = merged


class TransformationSequence:
    """A sequence of transformers executed in order."""

    def __init__(
        self, transformers: List[Transformer] = None, logger: Logger = None
    ) -> None:
        self._logger = logger
        self._transformers = transformers or []
        self._completed = False

    def add_transformer(self, transformer: Transformer) -> None:
        """Append a single transformer to the sequence."""
        self._transformers.append(transformer)

    def add_transformers(self, transformers: List[Transformer]) -> None:
        """Append multiple transformers to the sequence."""
        for transformer in transformers:
            self.add_transformer(transformer)

    def run_transformation(
        self, data: dict[str, pd.DataFrame]
    ) -> dict[str, pd.DataFrame]:
        """Run all transformers sequentially on a deepcopy of ``data``.

        Args:
            data: Mapping of tables to DataFrames.

        Returns:
            dict[str, pd.DataFrame]: Transformed copy of the input mapping.
        """
        transformed_data = deepcopy(data)
        for transformer in self._transformers:
            transformer.transform(transformed_data)

        return transformed_data
