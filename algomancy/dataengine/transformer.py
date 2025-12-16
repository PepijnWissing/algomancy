from abc import ABC, abstractmethod
import pandas as pd


class Transformer(ABC):
    def __init__(self, name: str = "Abstract Transformer", logger=None) -> None:
        self.name = name
        self._logger = logger

    @abstractmethod
    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        """Takes dict of dataframes and returns transformed dict"""
        pass


def fill_empty(data: pd.DataFrame) -> pd.DataFrame:
    return data.fillna(method="ffill", axis=1)


def drop_empty(data: pd.DataFrame) -> pd.DataFrame:
    return data.dropna()


class NoopTransformer(Transformer):
    def __init__(self, logger=None) -> None:
        super().__init__(name="No Operation Transformer", logger=logger)

    def transform(self, data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        if self._logger:
            self._logger.log("No operation transformer called")
        return data


class CleanTransformer(Transformer):
    def __init__(self, logger=None) -> None:
        super().__init__(name="Standard Transformer", logger=logger)

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        if self._logger:
            self._logger.log("Cleaning dataframes (dropna, lowercase columns)")
        for name, df in data.items():
            df = df.dropna()
            df.columns = [c.lower().strip() for c in df.columns]


class JoinTransformer(Transformer):
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
